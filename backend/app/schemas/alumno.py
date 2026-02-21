"""
Esquemas Pydantic para Alumno - Adaptado del sistema original.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class AlumnoBase(BaseModel):
    """Esquema base de alumno.
    
    GLOSARIO:
    - horario: Modalidad de asistencia del alumno (MATUTINO / VESPERTINO / DOBLE HORARIO)
    - turno: NO aplica al alumno. El turno (MAÑANA/TARDE) se registra en Asistencia.
    """
    dni: str
    nombres: str
    apell_paterno: str
    apell_materno: str
    fecha_nacimiento: Optional[date] = None
    
    # Datos académicos
    grupo: Optional[str] = None
    carrera: Optional[str] = None
    modalidad: Optional[str] = None
    horario: Optional[str] = None  # MATUTINO, VESPERTINO o DOBLE HORARIO
    grado: Optional[str] = None
    
    # Datos de padres
    nombre_padre_completo: Optional[str] = None
    celular_padre_1: Optional[str] = None
    celular_padre_2: Optional[str] = None
    descripcion: Optional[str] = None
    
    # Económico
    costo_matricula: Optional[float] = 0.0


class AlumnoCreate(AlumnoBase):
    """Esquema para crear alumno."""
    codigo_matricula: Optional[str] = None  # Ahora opcional, se genera automáticamente


class AlumnoUpdate(BaseModel):
    """Esquema para actualizar alumno."""
    nombres: Optional[str] = None
    apell_paterno: Optional[str] = None
    apell_materno: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    grupo: Optional[str] = None
    carrera: Optional[str] = None
    modalidad: Optional[str] = None
    horario: Optional[str] = None
    grado: Optional[str] = None
    nombre_padre_completo: Optional[str] = None
    celular_padre_1: Optional[str] = None
    celular_padre_2: Optional[str] = None
    descripcion: Optional[str] = None
    costo_matricula: Optional[float] = None
    activo: Optional[bool] = None


class AlumnoResponse(AlumnoBase):
    """Esquema de respuesta de alumno."""
    id: int
    codigo_matricula: str
    activo: bool
    fecha_registro: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AlumnoResumen(BaseModel):
    """Esquema resumido para listados."""
    id: int
    codigo_matricula: str
    dni: str
    nombre_completo: str
    grupo: Optional[str] = None
    activo: bool
    
    class Config:
        from_attributes = True
