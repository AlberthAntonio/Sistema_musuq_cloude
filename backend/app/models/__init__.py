"""
Módulo de modelos SQLAlchemy.
Exporta todos los modelos para facilitar importaciones.
"""
from app.models.usuario import Usuario
from app.models.alumno import Alumno
from app.models.asistencia import Asistencia
from app.models.curso import Curso, MallaCurricular
from app.models.aula import Aula, AulaGrupo, AulaCurso
from app.models.docente import Docente
from app.models.docente_curso import DocenteCurso
from app.models.evento import EventoCalendario
from app.models.horario import Horario
from app.models.plantilla_horario import PlantillaHorario, PlantillaBloque
from app.models.lista import ListaGuardada, lista_items
from app.models.sesion import SesionExamen
from app.models.nota import Nota
from app.models.periodo import PeriodoAcademico
from app.models.matricula import Matricula
from app.models.obligacion import ObligacionPago
from app.models.pago import Pago

__all__ = [
    "Usuario",
    "Alumno",
    "Asistencia",
    "Curso",
    "MallaCurricular",
    "Aula",
    "AulaGrupo",
    "AulaCurso",
    "Docente",
    "DocenteCurso",
    "EventoCalendario",
    "Horario",
    "PlantillaHorario",
    "PlantillaBloque",
    "ListaGuardada",
    "lista_items",
    "SesionExamen",
    "Nota",
    "PeriodoAcademico",
    "Matricula",
    "ObligacionPago",
    "Pago",
]
