from typing import List, Dict, Tuple, Any, Optional
from datetime import datetime
from core.api_client import AlumnoClient, AsistenciaClient, MatriculasClient

# Estados normalizados según backend refactorizado
_ESTADO_PUNTUAL   = "PUNTUAL"
_ESTADO_TARDANZA  = "TARDANZA"
_ESTADO_FALTA     = "INASISTENCIA"  # El backend usa "Inasistencia" para faltas no justificadas

class AlumnoDTO:
    """DTO para que la vista pueda acceder con notación de punto.
    Acepta datos de alumno y, opcionalmente, de matrícula activa."""

    def __init__(self, alumno_data: Dict, matricula_data: Optional[Dict] = None):
        mat = matricula_data or {}

        self.id              = alumno_data.get("id")
        self.dni             = alumno_data.get("dni", "")
        self.nombres         = alumno_data.get("nombres", "").upper()
        self.apell_paterno   = alumno_data.get("apell_paterno", "").upper()
        self.apell_materno   = alumno_data.get("apell_materno", "").upper()
        self.activo          = alumno_data.get("activo", True)

        # Campos que migraron a Matricula
        self.codigo_matricula = mat.get("codigo_matricula", "").upper()
        self.grupo            = mat.get("grupo", "").upper()
        self.horario          = mat.get("horario", "").upper()
        self.carrera          = mat.get("carrera", "").upper()
        self.modalidad        = mat.get("modalidad", "").upper()

        # Nombre completo calculado
        raw_nombre = alumno_data.get(
            "nombre_completo",
            f"{self.apell_paterno} {self.apell_materno}, {self.nombres}".strip(", ")
        )
        self.nombre_completo = raw_nombre.upper()

class ReporteAsistenciaController:
    """
    Controlador para reportes de asistencia.
    Conecta con el backend via APIClient.
    """
    
    def __init__(self, auth_token: str = ""):
        self.alumno_client     = AlumnoClient()
        self.asistencia_client = AsistenciaClient()
        self.matricula_client  = MatriculasClient()
        if auth_token:
            self.alumno_client.token     = auth_token
            self.asistencia_client.token = auth_token
            self.matricula_client.token  = auth_token

    def buscar_alumnos(self, texto: str) -> List[AlumnoDTO]:
        """Busca alumnos y retorna objetos DTO"""
        if not texto or len(texto) < 2: 
            return []
            
        success, result = self.alumno_client.buscar(texto)
        if success:
            # Manejar tanto lista directa como diccionario con "items"
            if isinstance(result, list):
                alumnos = result
            elif isinstance(result, dict):
                alumnos = result.get("items", [])
            else:
                alumnos = []
            
            return [AlumnoDTO(a) for a in alumnos]
        return []

    def obtener_perfil_completo(self, id_alumno: int, f_ini: str, f_fin: str) -> Tuple[bool, str, Dict]:
        """Retorna datos completos del alumno y su historial"""
        
        # 1. Obtener Alumno
        success_a, data_alumno = self.alumno_client.obtener_por_id(id_alumno)
        if not success_a:
            return False, "Error al obtener datos del alumno", {}

        # 1b. Obtener matrícula activa para completar datos académicos
        matricula_data: Dict = {}
        ok_m, mat = self.matricula_client.obtener_activa_por_alumno(id_alumno)
        if ok_m and isinstance(mat, dict):
            matricula_data = mat

        alumno_dto = AlumnoDTO(data_alumno, matricula_data)

        # 2. Obtener Historial (Usando filtros de fecha)
        # Convertir fechas de dd/mm/yyyy a yyyy-mm-dd para la API si es necesario
        # Asumiremos que el DateEntry entrega dd/mm/yyyy y la API espera yyyy-mm-dd
        try:
            d_ini = datetime.strptime(f_ini, "%d/%m/%Y").strftime("%Y-%m-%d")
            d_fin = datetime.strptime(f_fin, "%d/%m/%Y").strftime("%Y-%m-%d")
        except:
             return False, "Formato de fecha inválido", {}

        success_h, result_hist = self.asistencia_client.listar(
            alumno_id=id_alumno,
            fecha_inicio=d_ini,
            fecha_fin=d_fin
        )
        
        historial = []
        if success_h:
            historial = result_hist if isinstance(result_hist, list) else result_hist.get("items", [])

        # Normalizar campos a mayúsculas al salir del controlador
        for item in historial:
            if item.get("turno"):
                item["turno"] = item["turno"].upper()
            if item.get("estado"):
                item["estado"] = item["estado"].upper()

        # Ordenar historial por fecha y hora descendente (más reciente primero)
        historial.sort(key=lambda x: (x.get("fecha") or "", x.get("hora") or ""), reverse=True)

        # 3. Calcular Stats (comparar con constantes ya en mayúsculas)
        cont_p = sum(1 for h in historial if h.get("estado") == _ESTADO_PUNTUAL)
        cont_t = sum(1 for h in historial if h.get("estado") == _ESTADO_TARDANZA)
        cont_f = sum(1 for h in historial if h.get("estado") == _ESTADO_FALTA)
        total = len(historial)
        
        # Efectividad: (Puntuales + Tardanzas) / Total * 100 
        # Considerando que tardanza cuenta como asistencia pero penalizada. 
        # O si se desea solo puntualidad. Usualmente es asistencia total.
        asistencias_totales = cont_p + cont_t
        efect = int((asistencias_totales / total) * 100) if total > 0 else 0

        datos = {
            "alumno": alumno_dto,
            "historial": historial,
            "stats": {
                "puntual": cont_p,
                "tardanza": cont_t,
                "falta": cont_f,
                "efectividad": efect
            }
        }
        
        return True, "Datos cargados correctamente", datos