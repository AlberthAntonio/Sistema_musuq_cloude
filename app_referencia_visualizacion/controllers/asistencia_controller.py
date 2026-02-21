# app/controllers/asistencia_controller.py (REEMPLAZAR COMPLETO)

from datetime import datetime, time
from app.database import SessionLocal
from app.models.alumno_model import Alumno
from app.models.asistencia_model import Asistencia
from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload

class AsistenciaController:
    """
    Controller con detección de turno cruzado y alertas
    """
    
    def __init__(self):
        self.db = SessionLocal()
    
    def registrar_por_dni(self, codigo_input):
        """
        Registra asistencia con detección de turno cruzado
        
        Retorna: (exito, mensaje, datos, requiere_alerta)
        """
        # 1. Limpiar entrada
        codigo_input = codigo_input.strip().upper()
        
        if not codigo_input:
            return False, "Código vacío", {}, False
        
        # 2. Buscar alumno
        alumno = self.db.query(Alumno).filter(
            (Alumno.dni == codigo_input) | (Alumno.codigo_matricula == codigo_input)
        ).first()
        
        if not alumno:
            return False, "❌ Alumno no encontrado\nVerifique DNI o Código", {}, False
        
        # 3. Obtener hora actual y detectar turno activo
        ahora = datetime.now()
        hora_actual = ahora.time()
        fecha_actual = ahora.date()
        
        turno_detectado = self._detectar_turno_actual(hora_actual)
        
        if not turno_detectado:
            return False, "⚠️ FUERA DE HORARIO\nNo se puede registrar asistencia en este momento", {}, False
        
        # 4. Verificar si ya marcó EN ESTE TURNO hoy
        existe = self.db.query(Asistencia).filter(
            Asistencia.alumno_id == alumno.id,
            Asistencia.fecha == fecha_actual,
            Asistencia.turno == turno_detectado
        ).first()
        
        if existe:
            hora_str = existe.hora.strftime('%H:%M')
            return False, f"⚠️ Ya registró en turno {turno_detectado}\nHora: {hora_str}", {}, False
        
        # 5. Calcular estado según turno detectado
        estado = self._calcular_estado_segun_turno(hora_actual, turno_detectado)
        
        # 6. NORMALIZAR HORARIO DEL ALUMNO (CLAVE PARA EVITAR EL BUG)
        horario_alumno = self._normalizar_horario(getattr(alumno, 'horario', None))
        
        # 7. DETECCIÓN DE TURNO CRUZADO (mejorada)
        requiere_alerta = self._validar_turno_cruzado(horario_alumno, turno_detectado)

        # 8. Preparar datos para retornar (sin guardar aún si hay alerta)
        datos = {
            "alumno_obj": alumno,
            "id": None,
            "nombre": f"{alumno.nombres} {alumno.apell_paterno}",
            "alumno": f"{alumno.apell_paterno} {alumno.apell_materno}, {alumno.nombres}",
            "hora": hora_actual.strftime("%H:%M:%S"),
            "estado": estado,
            "codigo": alumno.codigo_matricula,
            "turno": turno_detectado,
            "horario": horario_alumno,  # Ya normalizado
            "fecha": fecha_actual,
            "hora_obj": hora_actual
        }
        
        # 9. Si requiere alerta, NO guardar aún (esperar confirmación)
        if requiere_alerta:
            return True, "ALERTA_TURNO_CRUZADO", datos, True
        
        # 10. Si no hay alerta, guardar directamente
        return self._guardar_asistencia(datos, alerta_turno=False)

    def _normalizar_horario(self, horario_raw):
        """
        Normaliza el campo turno para evitar problemas de formato
        
        Entrada: "Doble Turno", "doble turno", "  DOBLE HORARIO  ", None, ""
        Salida: "DOBLE HORARIO", "MATUTINO", "VESPERTINO"
        """
        if not horario_raw:
            return "MATUTINO"  # Por defecto si es NULL o vacío
        
        # Limpiar y convertir a mayúsculas
        horario_limpio = str(horario_raw).strip().upper()
        
        # Normalizar variantes
        if "DOBLE" in horario_limpio:
            return "DOBLE HORARIO"
        elif "MATUTINO" in horario_limpio or "MATURINO" in horario_limpio:
            return "MATUTINO"
        elif "VESPERTINO" in horario_limpio or "VESPERTINO" in horario_limpio:
            return "VESPERTINO"
        else:
            # Valor desconocido, asumir mañana
            print(f"⚠️ Horario desconocido: '{horario_raw}' - Asignando MATUTINO por defecto")
            return "MATUTINO"

    def _detectar_turno_actual(self, hora):
        """
        Detecta el turno según la hora actual del sistema
        
        TURNO MAÑANA: 6:00 AM - 11:59 AM
        TURNO TARDE: 1:00 PM - 11:59 PM
        FUERA: Resto de horarios
        """
        if time(6, 0, 0) <= hora < time(12, 0, 0):
            return "MAÑANA"
        elif time(13, 0, 0) <= hora <= time(23, 59, 59):
            return "TARDE"
        else:
            return None  # Fuera de horario
    
    def _calcular_estado_segun_turno(self, hora, turno):
        """
        Calcula PUNTUAL, TARDANZA o INASISTENCIA según turno
        
        MAÑANA:
        - 6:00-7:00 = PUNTUAL
        - 7:01-9:30 = TARDANZA
        - 9:31+ = INASISTENCIA
        
        TARDE:
        - 13:00-16:00 = PUNTUAL
        - 16:01-18:20 = TARDANZA
        - 18:21+ = INASISTENCIA
        """
        if turno == "MAÑANA":
            if hora <= time(7, 0, 0):
                return "PUNTUAL"
            elif hora <= time(9, 30, 0):
                return "TARDANZA"
            else:
                return "INASISTENCIA"
        
        elif turno == "TARDE":
            if hora <= time(16, 0, 0):
                return "PUNTUAL"
            elif hora <= time(18, 20, 0):
                return "TARDANZA"
            else:
                return "INASISTENCIA"
    
    def _validar_turno_cruzado(self, horario_matricula, turno_detectado):
        """
        Verifica si el alumno está marcando en un turno diferente al suyo
        
        LÓGICA CORRECTA:
        - MATUTINO → Solo puede marcar en turno MAÑANA
        - VESPERTINO → Solo puede marcar en turno TARDE
        - DOBLE HORARIO → Puede marcar en cualquier turno
        
        Args:
            horario_matricula: "MATUTINO", "VESPERTINO", "DOBLE HORARIO"
            turno_detectado: "MAÑANA", "TARDE"
        
        Returns:
            True: Hay conflicto (requiere alerta)
            False: Todo OK
        """
        
        # DEBUG: Descomentar para ver qué está pasando
        # print(f"🔍 Validando: horario='{horario_matricula}' vs turno='{turno_detectado}'")
        
        # 1. Si tiene DOBLE HORARIO, NUNCA hay alerta
        if horario_matricula == "DOBLE HORARIO":
            return False
        
        # 2. MAPEO: Convertir HORARIO → TURNO esperado
        if horario_matricula == "MATUTINO":
            turno_esperado = "MAÑANA"
        elif horario_matricula == "VESPERTINO":
            turno_esperado = "TARDE"
        else:
            # Horario desconocido, no generar alerta (ya se normalizó antes)
            return False
        
        # 3. Comparar turno esperado con el detectado
        if turno_detectado == turno_esperado:
            return False  # ✅ Marca en su horario correcto
        else:
            return True   # ⚠️ Marca en horario equivocado → ALERTA

    
    def guardar_con_confirmacion(self, datos, confirmado_por_personal):
        """
        Guarda asistencia después de confirmación del personal
        Se llama desde la vista cuando aceptan la alerta
        """
        return self._guardar_asistencia(datos, alerta_turno=confirmado_por_personal)
    
    def _guardar_asistencia(self, datos, alerta_turno=False):
        """
        Guarda el registro en BD
        """
        try:
            nueva_asistencia = Asistencia(
                alumno_id=datos["alumno_obj"].id,
                fecha=datos["fecha"],
                hora=datos["hora_obj"],
                estado=datos["estado"],
                turno=datos["turno"],
                alerta_turno=alerta_turno  # Marcar si hubo alerta
            )
            
            self.db.add(nueva_asistencia)
            self.db.commit()
            
            # Actualizar ID en datos
            datos["id"] = nueva_asistencia.id
            
            return True, f"✅ Asistencia Registrada: {datos['estado']}", datos, False
        
        except Exception as e:
            self.db.rollback()
            return False, f"Error al guardar: {str(e)}", {}, False
    
    def obtener_asistencias_hoy(self):
        """Devuelve asistencias del día actual"""
        fecha_hoy = datetime.now().date()
        return self.db.query(Asistencia)\
            .options(joinedload(Asistencia.alumno))\
            .filter(Asistencia.fecha == fecha_hoy)\
            .order_by(Asistencia.hora.desc())\
            .all()

# REEMPLAZAR EL MÉTODO marcar_inasistencias_automaticas() COMPLETO:

    def marcar_inasistencias_automaticas(self, turno_especifico=None):
        """
        Marca inasistencias SOLO para alumnos del turno correspondiente
        
        Args:
            turno_especifico: "MAÑANA" o "TARDE" (si es None, detecta automáticamente)
        
        Returns:
            (exito, mensaje, datos_resumen)
        """
        from datetime import datetime, date, time
        
        fecha_hoy = date.today()
        hora_actual = datetime.now().time()
        
        # 1. Detectar turno a cerrar (automático o manual)
        if turno_especifico:
            turno_a_cerrar = turno_especifico.upper()
        else:
            # Detección automática según hora
            if hora_actual < time(12, 0, 0):
                turno_a_cerrar = "MAÑANA"
            else:
                turno_a_cerrar = "TARDE"
        
        # 2. Validar turno
        if turno_a_cerrar not in ["MAÑANA", "TARDE"]:
            return False, "Turno inválido", {}
        
        try:
            # 3. Obtener alumnos que DEBEN asistir a este turno
            if turno_a_cerrar == "MAÑANA":
                alumnos_objetivo = self.db.query(Alumno).filter(
                    or_(
                        Alumno.horario == "MATUTINO",
                        Alumno.horario == "DOBLE HORARIO"
                    )
                ).all()
            elif turno_a_cerrar == "TARDE":
                alumnos_objetivo = self.db.query(Alumno).filter(
                    or_(
                        Alumno.horario == "VESPERTINO",
                        Alumno.horario == "DOBLE HORARIO"
                    )
                ).all()
            
            # 4. Filtrar quiénes ya tienen registro en este turno
            alumnos_sin_registro = []
            
            for alumno in alumnos_objetivo:
                # Verificar si ya marcó EN ESTE TURNO hoy
                registro_existe = self.db.query(Asistencia).filter(
                    Asistencia.alumno_id == alumno.id,
                    Asistencia.fecha == fecha_hoy,
                    Asistencia.turno == turno_a_cerrar
                ).first()
                
                if not registro_existe:
                    alumnos_sin_registro.append(alumno)
            
            # 5. Preparar resumen ANTES de marcar 
            horario_alumno = self._normalizar_horario(alumno.horario) if alumnos_sin_registro else None
            
            resumen = {
                "turno_cerrado": turno_a_cerrar,
                "total_alumnos_turno": len(alumnos_objetivo),
                "total_presentes": len(alumnos_objetivo) - len(alumnos_sin_registro),
                "total_a_marcar": len(alumnos_sin_registro),
                "alumnos_sin_registro": [
                    {
                        "id": a.id,
                        "codigo": a.codigo_matricula,
                        "nombre": f"{a.apell_paterno} {a.apell_materno}, {a.nombres}",
                        "horario": self._normalizar_horario(a.horario)
                    }
                    for a in alumnos_sin_registro
                ],
                "desglose": self._calcular_desglose(alumnos_sin_registro)
            }
            
            # 6. Si no hay nadie que marcar, retornar éxito sin hacer nada
            if len(alumnos_sin_registro) == 0:
                return True, f"✅ Turno {turno_a_cerrar} ya cerrado\nTodos los alumnos tienen registro", resumen
            
            # 7. Retornar resumen para confirmación (NO marcar aún)
            return True, "REQUIERE_CONFIRMACION", resumen
        
        except Exception as e:
            return False, f"Error al procesar: {str(e)}", {}

    def confirmar_cierre_turno(self, resumen):
        """
        Ejecuta el marcado de inasistencias después de la confirmación
        
        Args:
            resumen: dict con datos del cierre
        
        Returns:
            (exito, mensaje)
        """
        from datetime import date, time as dt_time
        
        try:
            fecha_hoy = date.today()
            turno_a_cerrar = resumen["turno_cerrado"]
            alumnos_sin_registro = resumen["alumnos_sin_registro"]
            
            contador = 0
            
            for alumno_data in alumnos_sin_registro:
                # Crear registro de inasistencia
                nueva_inasistencia = Asistencia(
                    alumno_id=alumno_data["id"],
                    fecha=fecha_hoy,
                    hora=dt_time(0, 0, 0),  # 00:00:00 indica cierre automático
                    estado="INASISTENCIA",
                    turno=turno_a_cerrar,
                    alerta_turno=False
                )
                
                self.db.add(nueva_inasistencia)
                contador += 1
            
            self.db.commit()
            
            return True, f"✅ Turno {turno_a_cerrar} cerrado exitosamente\n{contador} inasistencias marcadas"
        
        except Exception as e:
            self.db.rollback()
            return False, f"Error al guardar: {str(e)}"

    def _calcular_desglose(self, alumnos):
        """
        Calcula cuántos alumnos son de cada tipo de turno
        """
        desglose = {
            "MAÑANA": 0,
            "TARDE": 0,
            "DOBLE HORARIO": 0
        }
        
        for alumno in alumnos:
            turno_norm = self._normalizar_horario(alumno.horario)
            if turno_norm in desglose:
                desglose[turno_norm] += 1
        
        return desglose

    def obtener_estado_cierre_hoy(self):
        """
        Verifica qué turnos ya fueron cerrados hoy
        
        Returns:
            {
                "fecha": date,
                "manana_cerrado": bool,
                "tarde_cerrado": bool,
                "manana_cantidad": int,
                "tarde_cantidad": int
            }
        """
        from datetime import date, time as dt_time
        
        try:
            fecha_hoy = date.today()
            
            # Buscar registros automáticos (hora 00:00:00) de hoy
            cierres = self.db.query(Asistencia).filter(
                Asistencia.fecha == fecha_hoy,
                Asistencia.hora == dt_time(0, 0, 0),
                Asistencia.estado == "INASISTENCIA"
            ).all()
            
            manana_cerrado = any(c.turno == "MAÑANA" for c in cierres)
            tarde_cerrado = any(c.turno == "TARDE" for c in cierres)
            
            manana_cantidad = sum(1 for c in cierres if c.turno == "MAÑANA")
            tarde_cantidad = sum(1 for c in cierres if c.turno == "TARDE")
            
            return {
                "fecha": fecha_hoy,
                "manana_cerrado": manana_cerrado,
                "tarde_cerrado": tarde_cerrado,
                "manana_cantidad": manana_cantidad,
                "tarde_cantidad": tarde_cantidad
            }
        
        except Exception as e:
            print(f"Error verificando cierres: {e}")
            return {
                "fecha": fecha_hoy,
                "manana_cerrado": False,
                "tarde_cerrado": False,
                "manana_cantidad": 0,
                "tarde_cantidad": 0
            }

    def obtener_asistencias_hoy_por_turno(self, turno=None):
        """
        Obtiene asistencias del día actual, opcionalmente filtradas por turno
        Args:
            turno: "MAÑANA", "TARDE" o None (para todos)
        Returns:
            Lista de registros de asistencia
        """
        fecha_hoy = datetime.now().date()
        
        query = self.db.query(Asistencia)\
            .options(joinedload(Asistencia.alumno))\
            .filter(Asistencia.fecha == fecha_hoy)
        
        # Filtrar por turno si se especifica
        if turno:
            query = query.filter(Asistencia.turno == turno)
        
        return query.order_by(Asistencia.hora.desc()).all()

    def contar_alumnos_por_turno(self, horario1, horario2):
        """
        Cuenta alumnos que pertenecen a uno de dos horarios
        Args:
            horario1: Primer horario (ej: "MATUTINO")
            horario2: Segundo horario (ej: "DOBLE HORARIO")
        Returns:
            int: Total de alumnos
        """
        try:
            total = self.db.query(Alumno).filter(
                or_(
                    Alumno.horario == horario1,
                    Alumno.horario == horario2
                )
            ).count()
            return total
        except Exception as e:
            print(f"Error contando alumnos: {e}")
            return 0

    def contar_todos_alumnos(self):
        """Cuenta todos los alumnos activos"""
        try:
            return self.db.query(Alumno).count()
        except Exception as e:
            print(f"Error contando todos los alumnos: {e}")
            return 0




    def eliminar_asistencia(self, id_asistencia):
        """Elimina un registro"""
        try:
            registro = self.db.query(Asistencia).get(id_asistencia)
            if registro:
                self.db.delete(registro)
                self.db.commit()
                return True, "Registro eliminado"
            return False, "Registro no encontrado"
        except Exception as e:
            self.db.rollback()
            return False, f"Error: {str(e)}"
    
    def buscar_alumnos_general(self, texto_busqueda):
        """Búsqueda inteligente"""
        try:
            texto = texto_busqueda.strip().upper()
            if not texto:
                return []
            
            resultados = self.db.query(Alumno).filter(
                or_(
                    func.upper(Alumno.nombres).contains(texto),
                    func.upper(Alumno.apell_paterno).contains(texto),
                    func.upper(Alumno.apell_materno).contains(texto),
                    Alumno.dni.contains(texto),
                    func.upper(Alumno.codigo_matricula).contains(texto)
                )
            ).limit(15).all()
            
            return resultados
        except Exception as e:
            print(f"Error en búsqueda: {e}")
            return []
    
    def obtener_historial_alumno(self, alumno_id):
        """Historial completo"""
        try:
            return self.db.query(Asistencia).filter(
                Asistencia.alumno_id == alumno_id
            ).order_by(Asistencia.fecha.desc()).all()
        except Exception as e:
            print(f"Error historial: {e}")
            return []
    
    def justificar_asistencia(self, id_asistencia, motivo):
        """Justifica una inasistencia"""
        try:
            registro = self.db.query(Asistencia).get(id_asistencia)
            if registro:
                registro.estado = "JUSTIFICADO"
                if hasattr(registro, 'observacion'):
                    registro.observacion = motivo
                self.db.commit()
                return True, "Justificación guardada"
            return False, "Registro no encontrado"
        except Exception as e:
            self.db.rollback()
            return False, str(e)
