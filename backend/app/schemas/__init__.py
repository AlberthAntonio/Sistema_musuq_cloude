"""
Módulo de esquemas Pydantic.
Exporta todos los esquemas para facilitar importaciones.
"""
# Auth
from app.schemas.auth import (
    Token, TokenData, UsuarioCreate, UsuarioUpdate, 
    UsuarioResponse, LoginRequest
)

# Alumno
from app.schemas.alumno import (
    AlumnoBase, AlumnoCreate, AlumnoUpdate, 
    AlumnoResponse, AlumnoResumen
)

# Asistencia
from app.schemas.asistencia import (
    AsistenciaBase, AsistenciaCreate, AsistenciaUpdate,
    AsistenciaResponse, AsistenciaMasiva, AsistenciaReporte
)

# Curso
from app.schemas.curso import (
    CursoBase, CursoCreate, CursoUpdate, CursoResponse,
    MallaCurricularBase, MallaCurricularCreate, MallaCurricularResponse
)

# Docente
from app.schemas.docente import (
    DocenteBase, DocenteCreate, DocenteUpdate,
    DocenteResponse, DocenteResumen
)

# Evento
from app.schemas.evento import (
    EventoBase, EventoCreate, EventoUpdate, EventoResponse
)

# Horario
from app.schemas.horario import (
    HorarioBase, HorarioCreate, HorarioUpdate,
    HorarioResponse, HorarioCompleto
)

# Lista
from app.schemas.lista import (
    ListaBase, ListaCreate, ListaUpdate,
    ListaAddAlumnos, ListaResponse, ListaConAlumnos
)

# Sesion
from app.schemas.sesion import (
    SesionBase, SesionCreate, SesionUpdate,
    SesionResponse, SesionConNotas
)

# Nota
from app.schemas.nota import (
    NotaBase, NotaCreate, NotaUpdate,
    NotaResponse, NotasMasivas, NotaConDetalle
)

# Pago
from app.schemas.pago import (
    PagoBase, PagoCreate, PagoUpdate,
    PagoResponse, PagoConAlumno, ResumenPagosAlumno
)
