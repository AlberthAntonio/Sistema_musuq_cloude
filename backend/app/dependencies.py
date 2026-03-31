"""
Dependency Injection Providers para FastAPI.
Aquí se orquestan los Repositorios y Servicios inyectables en los controladores.
"""
from fastapi import Depends
from app.repositories.alumno_repository import AlumnoRepository
from app.services.alumno_service import AlumnoService
from app.repositories.asistencia_repository import AsistenciaRepository
from app.services.asistencia_service import AsistenciaService
from app.repositories.matricula_repository import MatriculaRepository
from app.services.matricula_service import MatriculaService
from app.repositories.pago_repository import PagoRepository
from app.services.pago_service import PagoService

# Global Singleton Repos
_alumno_repository = AlumnoRepository()
_asistencia_repository = AsistenciaRepository()
_matricula_repository = MatriculaRepository()
_pago_repository = PagoRepository()

def get_alumno_repository() -> AlumnoRepository:
    """Devuelve el repositorio pre-instanciado."""
    return _alumno_repository

def get_alumno_service(repo: AlumnoRepository = Depends(get_alumno_repository)) -> AlumnoService:
    """Devuelve el servicio de Alumno con su respectivo repositorio inyectado."""
    return AlumnoService(repo=repo)

def get_asistencia_repository() -> AsistenciaRepository:
    """Devuelve repo asistencia."""
    return _asistencia_repository

def get_asistencia_service(repo: AsistenciaRepository = Depends(get_asistencia_repository)) -> AsistenciaService:
    return AsistenciaService(repo=repo)

def get_matricula_repository() -> MatriculaRepository:
    return _matricula_repository

def get_matricula_service(repo: MatriculaRepository = Depends(get_matricula_repository)) -> MatriculaService:
    return MatriculaService(repo=repo)

def get_pago_repository() -> PagoRepository:
    return _pago_repository

def get_pago_service(repo: PagoRepository = Depends(get_pago_repository)) -> PagoService:
    return PagoService(repo=repo)
