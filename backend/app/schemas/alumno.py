"""
Esquemas Pydantic para Alumno - Solo datos personales.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class AlumnoBase(BaseModel):
    """Esquema base de alumno - solo datos personales."""
    dni: str
    nombres: str
    apell_paterno: str
    apell_materno: str
    fecha_nacimiento: Optional[date] = None
    
    # Datos de padres
    nombre_padre_completo: Optional[str] = None
    celular_padre_1: Optional[str] = None
    celular_padre_2: Optional[str] = None
    descripcion: Optional[str] = None


class AlumnoCreate(AlumnoBase):
    """Esquema para crear alumno."""
    pass


class AlumnoUpdate(BaseModel):
    """Esquema para actualizar alumno."""
    nombres: Optional[str] = None
    apell_paterno: Optional[str] = None
    apell_materno: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    nombre_padre_completo: Optional[str] = None
    celular_padre_1: Optional[str] = None
    celular_padre_2: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class AlumnoResponse(AlumnoBase):
    """Esquema de respuesta de alumno."""
    id: int
    activo: bool
    creado_por: Optional[int] = None
    fecha_registro: Optional[datetime] = None
    codigo_matricula: Optional[str] = None
    horario: Optional[str] = None

    class Config:
        from_attributes = True


class AlumnoResumen(BaseModel):
    """Esquema resumido para listados."""
    id: int
    dni: str
    nombre_completo: str
    activo: bool
    
    class Config:
        from_attributes = True
