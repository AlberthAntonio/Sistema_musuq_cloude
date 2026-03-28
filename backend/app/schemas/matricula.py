"""
Esquemas Pydantic para Matrícula.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MatriculaBase(BaseModel):
    """Esquema base de matrícula."""
    alumno_id: int
    periodo_id: int
    grupo: Optional[str] = None
    carrera: Optional[str] = None
    modalidad: Optional[str] = None
    horario: Optional[str] = None
    nivel: Optional[str] = None
    grado: Optional[str] = None


class MatriculaCreate(MatriculaBase):
    """Esquema para crear matrícula. El código se genera automáticamente."""
    codigo_matricula: Optional[str] = None


class MatriculaUpdate(BaseModel):
    """Esquema para actualizar matrícula."""
    grupo: Optional[str] = None
    carrera: Optional[str] = None
    modalidad: Optional[str] = None
    horario: Optional[str] = None
    nivel: Optional[str] = None
    grado: Optional[str] = None
    estado: Optional[str] = None  # 'activo', 'retirado'


class MatriculaResponse(MatriculaBase):
    """Esquema de respuesta de matrícula."""
    id: int
    codigo_matricula: str
    estado: str
    creado_por: Optional[int] = None
    fecha_registro: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MatriculaConAlumno(MatriculaResponse):
    """Esquema con datos del alumno incluidos."""
    alumno_nombre: Optional[str] = None
    alumno_dni: Optional[str] = None
