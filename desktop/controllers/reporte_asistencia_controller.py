from typing import List, Dict, Tuple, Any
from datetime import datetime
from core.api_client import AlumnoClient, AsistenciaClient

class AlumnoDTO:
    """DTO para que la vista pueda acceder con notación de punto"""
    def __init__(self, data: Dict):
        self.id = data.get("id")
        
        self.nombre_completo = data.get("nombre_completo", "")
        
        self.nombres = data.get("nombres", "")
        self.apell_paterno = data.get("apell_paterno", "")
        self.apell_materno = data.get("apell_materno", "")

        self.dni = data.get("dni", "")
        self.codigo_matricula = data.get("codigo_matricula", "")
        self.grupo = data.get("grupo", "")
        self.horario = data.get("horario", "")
        self.activo = data.get("activo", True)

class ReporteAsistenciaController:
    """
    Controlador para reportes de asistencia.
    Conecta con el backend via APIClient.
    """
    
    def __init__(self):
        self.alumno_client = AlumnoClient()
        self.asistencia_client = AsistenciaClient()

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
            
        alumno_dto = AlumnoDTO(data_alumno)

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
        
        # Ordenar historial por fecha y hora descendente (más reciente primero)
        historial.sort(key=lambda x: (x.get("fecha") or "", x.get("hora") or ""), reverse=True)

        # 3. Calcular Stats
        cont_p = sum(1 for h in historial if h.get("estado") == "PUNTUAL")
        cont_t = sum(1 for h in historial if h.get("estado") == "TARDANZA")
        cont_f = sum(1 for h in historial if h.get("estado") in ["FALTA", "INASISTENCIA"])
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