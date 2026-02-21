from typing import Dict, List, Tuple, Optional, Any
from datetime import date, datetime, time as time_obj
from core.api_client import AlumnoClient, AsistenciaClient

class AsistenciaController:
    """Controlador para la gestión de asistencia"""
    
    def __init__(self, auth_token: str):
        self.alumno_client = AlumnoClient()
        self.asistencia_client = AsistenciaClient()
        
        # Cache para evitar traer 1000 alumnos solo para contar
        self._cache_total_alumnos = None
        self._cache_conteo_horario = {}
        
        self.alumno_client.token = auth_token
        self.asistencia_client.token = auth_token
        
    def get_alumnos_por_grupo(self, grupo: str) -> Tuple[bool, List[Dict]]:
        """Obtener alumnos de un grupo específico"""
        success, result = self.alumno_client.obtener_todos(limit=1000)
        if success:
            items = result if isinstance(result, list) else result.get("items", [])
            filtrados = [a for a in items if a.get("grupo") == grupo and a.get("activo", True)]
            filtrados.sort(key=lambda x: f"{x.get('apell_paterno', '')} {x.get('apell_materno', '')}")
            return True, filtrados
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
        """Contar alumnos activos según su horario asignado (MATUTINO, VESPERTINO, DOBLE HORARIO)"""
        # Cache key basado en los horarios
        cache_key = "_".join(sorted(horarios))
        if cache_key in self._cache_conteo_horario:
            return self._cache_conteo_horario[cache_key]
        
        success, result = self.alumno_client.obtener_todos(limit=1000)
        if success:
            items = result if isinstance(result, list) else result.get("items", [])
            count = 0
            for a in items:
                if not a.get("activo", True): continue
                # El campo horario del alumno contiene MATUTINO / VESPERTINO / DOBLE HORARIO
                horario_alumno = a.get("horario", "").upper()
                if any(h in horario_alumno for h in horarios):
                    count += 1
            self._cache_conteo_horario[cache_key] = count
            return count
        return 0

    def registrar_por_dni(self, codigo: str) -> Tuple[bool, str, Optional[Dict], bool]:
        """
        Registra asistencia buscando por DNI o Código.
        Retorna: (exito, mensaje, datos_registro, requiere_alerta_turno)
        """
        # 1. Buscar alumno
        # Primero intentamos por Código exacto (más rápido si fuera posible, pero usamos buscar general)
        alumnos = self.buscar_alumnos_general(codigo)
        
        if not alumnos:
            return False, "Alumno no encontrado", None, False
        
        # Si hay varios, tomamos el primero que coincida exactamente si es posible
        alumno = alumnos[0]
        # Refinar búsqueda exacta si hay múltiples resultados parciales
        for a in alumnos:
            if str(a.get("dni")) == codigo or a.get("codigo_matricula") == codigo:
                alumno = a
                break
        
        # 2. Verificar si ya marcó hoy
        hoy = date.today().isoformat()
        success, asistencias = self.asistencia_client.listar(fecha=hoy, alumno_id=alumno["id"])
        
        if success and asistencias:
             # Ya tiene asistencia
             primera = asistencias[0]
             hora = primera.get("hora", "??:??")
             return False, f"El alumno ya registró asistencia a las {hora}", None, False
        
        # 3. Determinar Estado y Turno Actual
        hora_actual = datetime.now().time()
        turno_actual = "MAÑANA" if hora_actual < time_obj(13, 0, 0) else "TARDE"
        
        # Lógica simple de estado (se puede mejorar con configuración Horarios)
        estado = "PUNTUAL"
        # Ej: Tarde después de las 8:15 o 13:15
        limite_tardanza_m = time_obj(8, 15, 0)
        limite_tardanza_t = time_obj(13, 15, 0)
        
        if turno_actual == "MAÑANA" and hora_actual > limite_tardanza_m:
            estado = "TARDANZA"
        elif turno_actual == "TARDE" and hora_actual > limite_tardanza_t:
            estado = "TARDANZA"
            
        # 4. Verificar Turno Cruzado
        horario_alumno = alumno.get("horario", "").upper() # MATUTINO / VESPERTINO / DOBLE
        alerta_turno = False
        
        if "MATUTINO" in horario_alumno and turno_actual == "TARDE":
            alerta_turno = True
        elif "VESPERTINO" in horario_alumno and turno_actual == "MAÑANA":
            alerta_turno = True
            
        # 5. Registrar
        payload = {
            "alumno_id": alumno["id"],
            "fecha": hoy,
            "hora": hora_actual.strftime("%H:%M:%S"),
            "turno": turno_actual,
            "estado": estado,
            "alerta_turno": alerta_turno
        }
        
        success, result = self.asistencia_client.registrar(payload)
        
        if success:
            # Enriquecer resultado con datos del alumno para la UI
            result["alumno"] = alumno # Para mostrar nombre en UI
            return True, "Asistencia registrada", result, alerta_turno
    
    def eliminar_asistencia(self, asistencia_id: int) -> Tuple[bool, str]:
        """Eliminar un registro de asistencia"""
        success, result = self.asistencia_client.eliminar(asistencia_id)
        if success:
            return True, "Registro eliminado correctamente"
        else:
            return False, result.get("error", "Error al eliminar el registro")


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
        success, result = self.asistencia_client.listar(alumno_id=alumno_id)
        if success:
             # result es una lista de dicts
            items = result if isinstance(result, list) else result.get("items", [])
            # Ordenar por fecha descendente
            items.sort(key=lambda x: (x.get("fecha") or "", x.get("hora") or ""), reverse=True)
            return items
        return []

