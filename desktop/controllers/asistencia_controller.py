from typing import Dict, List, Tuple, Optional, Any
from datetime import date, datetime, time as time_obj
from core.api_client import AlumnoClient, AsistenciaClient, MatriculasClient

# Estados normalizados según esquema backend
ESTADO_PUNTUAL  = "PUNTUAL"
ESTADO_TARDANZA = "TARDANZA"
ESTADO_FALTA    = "FALTA"
TURNO_MANANA    = "MAÑANA"
TURNO_TARDE     = "TARDE"

class AsistenciaController:
    """Controlador para la gestión de asistencia"""
    
    def __init__(self, auth_token: str):
        self.alumno_client = AlumnoClient()
        self.asistencia_client = AsistenciaClient()
        self.matricula_client = MatriculasClient()
        
        # Cache para evitar traer 1000 alumnos solo para contar
        self._cache_total_alumnos = None
        self._cache_conteo_horario = {}
        
        self.alumno_client.token = auth_token
        self.asistencia_client.token = auth_token
        self.matricula_client.token = auth_token
        
    def get_alumnos_por_grupo(self, grupo: str) -> Tuple[bool, List[Dict]]:
        """Obtener alumnos de un grupo — el filtro grupo se delega al backend (JOIN con matrículas)"""
        success, result = self.alumno_client.obtener_todos(limit=1000, grupo=grupo)
        if success:
            items = result if isinstance(result, list) else result.get("items", [])
            activos = [a for a in items if a.get("activo", True)]
            activos.sort(key=lambda x: f"{x.get('apell_paterno', '')} {x.get('apell_materno', '')}")
            return True, activos
        return False, []

    def buscar_alumnos_general(self, texto: str) -> List[Dict]:
        """
        Buscar alumnos por nombre, dni o código.
        
        Args:
            texto: Término de búsqueda
            
        Returns:
            Lista de alumnos encontrados (vacía si no hay resultados o error)
        """
        # Validación local
        if not texto or len(texto.strip()) < 2:
            print(f"[DEBUG Controller] Búsqueda muy corta: '{texto}'")
            return []
        
        print(f"[DEBUG Controller] Buscando: '{texto}'")
        success, result = self.alumno_client.buscar(texto)
        
        if success:
            # result ya es una lista
            resultados = result if isinstance(result, list) else []
            print(f"[DEBUG Controller] Resultados: {len(resultados)} encontrados")
            return resultados
        else:
            # Error en la búsqueda
            error_msg = result.get("error", "Error desconocido") if isinstance(result, dict) else str(result)
            print(f"[ERROR Controller] Búsqueda falló: {error_msg}")
        return []

    def contar_todos_alumnos(self) -> int:
        """Contar total de alumnos activos"""
        # Usar cache si está disponible
        if self._cache_total_alumnos is not None:
            return self._cache_total_alumnos
        
        success, result = self.alumno_client.obtener_todos(limit=1000)
        if success:
            items = result if isinstance(result, list) else result.get("items", [])
            count = len([a for a in items if a.get("activo", True)])
            self._cache_total_alumnos = count
            return count
        return 0

    def contar_alumnos_por_horario(self, *horarios) -> int:
        """Contar alumnos activos según horario en su matrícula (MATUTINO/VESPERTINO/DOBLE)"""
        cache_key = "_".join(sorted(h.upper() for h in horarios))
        if cache_key in self._cache_conteo_horario:
            return self._cache_conteo_horario[cache_key]

        success, result = self.matricula_client.listar(estado="activo", limit=1000)
        if success:
            items = result if isinstance(result, list) else []
            count = sum(
                1 for m in items
                if any(h.upper() in m.get("horario", "").upper() for h in horarios)
            )
            self._cache_conteo_horario[cache_key] = count
            return count
        return 0

    def registrar_por_dni(
        self,
        codigo: str,
        forzar_turno_cruzado: bool = False
    ) -> Tuple[bool, str, Optional[Dict], bool]:
        """
        Registra asistencia buscando por DNI o Código de matrícula.

        Retorna: (exito, mensaje, datos, alerta_turno)

        Reglas de negocio:
        ─────────────────────────────────────────────────────────────────
        MATUTINO    → 1 sola marca por día.  Turno natural: MAÑANA.
                      Si intenta marcar en TARDE → TURNO CRUZADO (alarma,
                      personal decide; si confirma se registra igualmente).

        VESPERTINO  → 1 sola marca por día.  Turno natural: TARDE.
                      Si intenta marcar en MAÑANA → TURNO CRUZADO (ídem).

        DOBLE HOR.  → 2 marcas por día: una en MAÑANA y otra en TARDE.
                      Se bloquea si ya marcó en el turno ACTUAL (no en día).
                      No genera turno cruzado (puede asistir a ambos).

        Caso especial (turno cruzado sin forzar):
          devuelve (False, "TURNO_CRUZADO_PENDIENTE", datos_dialogo, True)
          sin registrar. Si personal confirma, rellamar con forzar=True.
        ─────────────────────────────────────────────────────────────────
        """
        # ── 1. Buscar alumno ──────────────────────────────────────────
        alumnos = self.buscar_alumnos_general(codigo)
        if not alumnos:
            return False, "Alumno no encontrado", None, False

        alumno = alumnos[0]
        for a in alumnos:
            if str(a.get("dni")) == codigo or a.get("codigo_matricula") == codigo:
                alumno = a
                break

        hoy = date.today().isoformat()

        # ── 2. Obtener horario del alumno PRIMERO ─────────────────────
        # Necesitamos el horario antes de evaluar duplicados y turno cruzado.
        horario_alumno = (alumno.get("horario") or "").upper()
        if not horario_alumno:
            mat_ok, matricula = self.matricula_client.obtener_activa_por_alumno(alumno["id"])
            if mat_ok and matricula:
                horario_alumno = (matricula.get("horario") or "").upper()

        es_doble = "DOBLE" in horario_alumno

        # ── 3. Determinar turno y estado actuales ─────────────────────
        hora_actual = datetime.now().time()
        turno_actual = TURNO_MANANA if hora_actual < time_obj(13, 0, 0) else TURNO_TARDE

        estado = ESTADO_PUNTUAL
        if turno_actual == TURNO_MANANA and hora_actual > time_obj(8, 15, 0):
            estado = ESTADO_TARDANZA
        elif turno_actual == TURNO_TARDE and hora_actual > time_obj(13, 15, 0):
            estado = ESTADO_TARDANZA

        print(f"[DEBUG Controller] Turno actual: {turno_actual} | Horario alumno: '{horario_alumno}' | DobleHorario: {es_doble}")

        # ── 4. Verificar asistencias ya registradas hoy ───────────────
        ok_prev, asistencias_hoy = self.asistencia_client.listar(fecha=hoy, alumno_id=alumno["id"])
        asistencias_hoy = asistencias_hoy if (ok_prev and isinstance(asistencias_hoy, list)) else []

        if es_doble:
            # DOBLE HORARIO: solo bloquear si ya marcó en el turno actual
            ya_marco_este_turno = any(
                (a.get("turno") or "").upper() == turno_actual.upper()
                for a in asistencias_hoy
            )
            if ya_marco_este_turno:
                hora_prev = next(
                    (a.get("hora", "??:??") for a in asistencias_hoy
                     if (a.get("turno") or "").upper() == turno_actual.upper()),
                    "??:??"
                )
                return False, (
                    f"El alumno (DOBLE HORARIO) ya registró el turno {turno_actual} a las {hora_prev}"
                ), None, False
        else:
            # MATUTINO / VESPERTINO: bloquear si ya tiene cualquier registro hoy
            if asistencias_hoy:
                hora_prev = asistencias_hoy[0].get("hora", "??:??")
                turno_prev = (asistencias_hoy[0].get("turno") or "").upper()
                return False, (
                    f"El alumno ya registró asistencia hoy"
                    + (f" (turno {turno_prev} a las {hora_prev})" if turno_prev else f" a las {hora_prev}")
                ), None, False

        # ── 5. Evaluar turno cruzado (solo MATUTINO / VESPERTINO) ─────
        alerta_turno = False
        if not es_doble and horario_alumno:
            if "MATUTINO" in horario_alumno and turno_actual == TURNO_TARDE:
                alerta_turno = True
                print("[DEBUG Controller] ⚠️ TURNO CRUZADO: MATUTINO en TARDE")
            elif "VESPERTINO" in horario_alumno and turno_actual == TURNO_MANANA:
                alerta_turno = True
                print("[DEBUG Controller] ⚠️ TURNO CRUZADO: VESPERTINO en MAÑANA")

        # Si hay turno cruzado y aún no se forzó → la UI debe pedir confirmación
        if alerta_turno and not forzar_turno_cruzado:
            nombre = f"{alumno.get('nombres','')} {alumno.get('apell_paterno','')} {alumno.get('apell_materno','')}".strip()
            datos_dialogo = {
                "alumno":       nombre,
                "codigo":       alumno.get("codigo_matricula") or codigo,
                "horario":      horario_alumno,
                "turno":        turno_actual,
                "estado":       estado,
                "hora":         hora_actual.strftime("%H:%M:%S"),
                "_alumno_obj":  alumno,
                "_hoy":         hoy,
                "_hora_actual": hora_actual,
            }
            return False, "TURNO_CRUZADO_PENDIENTE", datos_dialogo, True

        # ── 6. Registrar ──────────────────────────────────────────────
        payload = {
            "alumno_id":   alumno["id"],
            "fecha":       hoy,
            "hora":        hora_actual.strftime("%H:%M:%S"),
            "turno":       turno_actual,
            "estado":      estado,
            "alerta_turno": alerta_turno,
        }

        success, result = self.asistencia_client.registrar(payload)
        if success:
            result["alumno"] = alumno
            return True, "Asistencia registrada", result, alerta_turno

        error_msg = result.get("error", "Error al registrar asistencia") if isinstance(result, dict) else str(result)
        return False, error_msg, None, False

    def eliminar_asistencia(self, asistencia_id: int) -> Tuple[bool, str]:
        """Eliminar un registro de asistencia"""
        success, result = self.asistencia_client.eliminar(asistencia_id)
        if success:
            return True, "Registro eliminado correctamente"
        else:
            return False, result.get("error", "Error al eliminar el registro")

    def previsualizar_inasistencias(self, turno: str) -> Tuple[bool, str, dict]:
        """
        Calcula el resumen de inasistencias pendientes para el turno indicado
        SIN registrar nada. Devuelve los datos que necesita el diálogo.

        Returns:
            (exito, mensaje_error, resumen_dict)
            resumen_dict = {
                "turno": str,
                "total_alumnos_turno": int,
                "total_presentes": int,
                "total_a_marcar": int,
                "alumnos_sin_registro": [{"nombre": str, "codigo": str, "horario": str}]
            }
        """
        horarios_turno = ["MATUTINO", "DOBLE HORARIO"] if turno == "MAÑANA" else ["VESPERTINO", "DOBLE HORARIO"]

        # 1. Matrículas activas del turno
        ok_mat, result_mat = self.matricula_client.listar(estado="activo", limit=2000)
        if not ok_mat:
            return False, "No se pudo obtener la lista de matrículas", {}

        matriculas = result_mat if isinstance(result_mat, list) else []
        # Mapa alumno_id → horario para este turno
        mapa_horario = {
            m["alumno_id"]: m.get("horario", "")
            for m in matriculas
            if any(h.upper() in m.get("horario", "").upper() for h in horarios_turno)
        }
        ids_turno = set(mapa_horario.keys())

        # 2. Asistencias de hoy para el turno
        ok_hoy, result_hoy = self.asistencia_client.obtener_hoy(turno=turno)
        if not ok_hoy:
            return False, "No se pudo obtener la asistencia de hoy", {}

        asistencias_hoy = result_hoy if isinstance(result_hoy, list) else result_hoy.get("items", [])
        ids_presentes = {a["alumno_id"] for a in asistencias_hoy}

        # 3. Faltantes
        ids_faltantes = ids_turno - ids_presentes

        # 4. Enriquecer con datos del alumno si tenemos el mapa en caché
        alumnos_sin_registro = []
        if hasattr(self, "mapa_alumnos"):
            for aid in ids_faltantes:
                a = self.mapa_alumnos.get(aid, {})
                nombre = f"{a.get('nombres', '')} {a.get('apell_paterno', '')} {a.get('apell_materno', '')}".strip()
                alumnos_sin_registro.append({
                    "nombre": nombre or f"Alumno {aid}",
                    "codigo": a.get("codigo_matricula", ""),
                    "horario": mapa_horario.get(aid, ""),
                })
        else:
            alumnos_sin_registro = [
                {"nombre": f"Alumno {aid}", "codigo": "", "horario": mapa_horario.get(aid, "")}
                for aid in ids_faltantes
            ]

        alumnos_sin_registro.sort(key=lambda x: x["nombre"])

        resumen = {
            "turno": turno,
            "total_alumnos_turno": len(ids_turno),
            "total_presentes": len(ids_presentes),
            "total_a_marcar": len(ids_faltantes),
            "alumnos_sin_registro": alumnos_sin_registro,
        }
        return True, "", resumen

    def marcar_inasistencias_masivo(self, turno: str) -> Tuple[bool, str, int]:
        """
        Marca como FALTA a todos los alumnos que correspondan al turno indicado
        y que aún NO tienen registro de asistencia hoy.

        Args:
            turno: "MAÑANA" o "TARDE"

        Returns:
            (exito, mensaje, cantidad_registros_creados)
        """
        from datetime import date, datetime

        hoy = date.today().isoformat()
        hora_ahora = datetime.now().strftime("%H:%M:%S")

        # 1. Obtener alumnos activos del turno correspondiente
        horarios_turno = ["MATUTINO", "DOBLE HORARIO"] if turno == "MAÑANA" else ["VESPERTINO", "DOBLE HORARIO"]

        ok_mat, result_mat = self.matricula_client.listar(estado="activo", limit=2000)
        if not ok_mat:
            return False, "No se pudo obtener la lista de matrículas", 0

        matriculas = result_mat if isinstance(result_mat, list) else []
        alumno_ids_turno = {
            m["alumno_id"]
            for m in matriculas
            if any(h.upper() in m.get("horario", "").upper() for h in horarios_turno)
        }

        if not alumno_ids_turno:
            return False, "No hay alumnos registrados para este turno", 0

        # 2. Obtener asistencias de hoy para ese turno
        ok_hoy, result_hoy = self.asistencia_client.obtener_hoy(turno=turno)
        if not ok_hoy:
            return False, "No se pudo obtener la asistencia de hoy", 0

        asistencias_hoy = result_hoy if isinstance(result_hoy, list) else result_hoy.get("items", [])
        ids_ya_marcados = {a["alumno_id"] for a in asistencias_hoy}

        # 3. Calcular quiénes faltan
        ids_faltantes = alumno_ids_turno - ids_ya_marcados

        if not ids_faltantes:
            return True, "Todos los alumnos del turno ya tienen asistencia registrada", 0

        # 4. Registrar FALTA en masa
        registros = [
            {
                "alumno_id": alumno_id,
                "fecha": hoy,
                "hora": hora_ahora,
                "turno": turno,
                "estado": ESTADO_FALTA,
                "alerta_turno": False
            }
            for alumno_id in ids_faltantes
        ]

        payload = {"fecha": hoy, "turno": turno, "registros": registros}
        ok_masivo, result_masivo = self.asistencia_client.registrar_masivo(payload)

        if ok_masivo:
            return True, f"Se marcaron {len(ids_faltantes)} inasistencias correctamente", len(ids_faltantes)
        else:
            error_msg = result_masivo.get("error", "Error desconocido") if isinstance(result_masivo, dict) else str(result_masivo)
            return False, f"Error al registrar inasistencias: {error_msg}", 0


    def get_asistencia_hoy(self, grupo: str, turno: str) -> Dict[int, str]:
        """Obtener mapa de asistencias de hoy {alumno_id: estado}"""
        success, result = self.asistencia_client.obtener_hoy(grupo, turno)
        mapa = {}
        if success:
            for asist in result:
                mapa[asist["alumno_id"]] = asist["estado"]
        return mapa

    def guardar_asistencia_masiva(self, fecha: str, turno: str, registros: List[Dict]) -> Tuple[bool, Dict]:
        """
        Guardar asistencia masiva
        registros: [{"alumno_id": 1, "estado": "Puntual", "observacion": "..."}]
        """
        payload = {
            "fecha": fecha,
            "turno": turno,
            "registros": registros
        }
        return self.asistencia_client.registrar_masivo(payload)

    def justificar_asistencia(self, id_asistencia: int, motivo: str) -> Tuple[bool, str]:
        """
        Justificar una inasistencia o tardanza.
        """
        success, result = self.asistencia_client.justificar(id_asistencia, motivo)
        if success:
            return True, "Justificación registrada exitosamente"
        else:
            return False, result.get("error", "Error al justificar")

    def obtener_historial_alumno(self, alumno_id: int) -> List[Dict]:
        """Obtener historial completo de un alumno"""
        # limit=10000 para traer todos los registros del alumno sin truncar
        success, result = self.asistencia_client.listar(alumno_id=alumno_id, limit=10000)
        if success:
             # result es una lista de dicts
            items = result if isinstance(result, list) else result.get("items", [])
            # Normalizar valores a mayúsculas al salir del controlador
            for item in items:
                if "turno" in item and item["turno"]:
                    item["turno"] = item["turno"].upper()
                if "estado" in item and item["estado"]:
                    item["estado"] = item["estado"].upper()
            # Ordenar por fecha descendente
            items.sort(key=lambda x: (x.get("fecha") or "", x.get("hora") or ""), reverse=True)
            return items
        return []

