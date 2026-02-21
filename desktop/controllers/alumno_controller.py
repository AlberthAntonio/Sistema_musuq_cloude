from typing import Dict, Tuple, List, Optional
from core.api_client import AlumnoClient

class AlumnoController:
    """Controlador para la gestión de alumnos (Lógica de Negocio)"""
    
    def __init__(self, auth_token: str):
        self.alumno_client = AlumnoClient()
        self.alumno_client.token = auth_token
        
        # Carreras por grupo (Business Logic)
        self.CARRERAS_POR_GRUPO = {
            "A": ["MEDICINA", "ENFERMERÍA", "ODONTOLOGÍA", "FARMACIA", "OBSTETRICIA"],
            "B": ["DERECHO", "ADMINISTRACIÓN", "CONTABILIDAD", "ECONOMÍA", "TURISMO"],
            "C": ["INGENIERÍA CIVIL", "ARQUITECTURA", "ING. SISTEMAS", "ING. INDUSTRIAL", "ING. AMBIENTAL"],
            "D": ["EDUCACIÓN INICIAL", "EDUCACIÓN PRIMARIA", "PSICOLOGÍA", "CIENCIAS COMUNICACIÓN", "TRABAJO SOCIAL"]
        }
    
    def get_carreras_por_grupo(self, grupo: str) -> List[str]:
        """Obtener lista de carreras para un grupo"""
        return self.CARRERAS_POR_GRUPO.get(grupo, [])
        
    def calcular_deuda(self, costo: float, a_cuenta: float) -> float:
        """Calcular deuda"""
        return max(0.0, costo - a_cuenta)
        
    def create_student(self, data: Dict) -> Tuple[bool, Dict]:
        """Crear un nuevo alumno en el backend"""
        return self.alumno_client.crear(data)
        
    def get_recent_students(self, limit: int = 5) -> Tuple[bool, object]:
        """Obtener últimos alumnos registrados"""
        return self.alumno_client.obtener_todos(limit=limit)

    def validate_student_data(self, data: Dict) -> Tuple[bool, str, Optional[str]]:
        """
        Validar datos del alumno antes de enviar.
        Retorna: (EsValido, MensajeError, CampoError)
        """
        # DNI
        if not data.get("dni") or len(data.get("dni", "")) != 8:
            return False, "El DNI debe tener 8 dígitos", "dni"
        
        # Nombres
        if not data.get("nombres"):
            return False, "Falta el nombre", "nombres"
            
        if not data.get("apell_paterno"):
            return False, "Falta apellido paterno", "apellido_paterno"
            
        # Grupo
        if not data.get("grupo") or data.get("grupo") == "--Seleccione":
            return False, "Debe seleccionar un Grupo", "grupo"
            
        # Carrera
        if not data.get("carrera") or data.get("carrera") == "--Seleccione":
            return False, "Debe seleccionar una Carrera", "carrera"
            
        # Costo
        try:
            c = float(data.get("costo_matricula", 0) or 0)
            if c < 0:
                return False, "El costo no puede ser negativo", "costo"
        except:
            return False, "Costo inválido", "costo"
            
        return True, "OK", None
