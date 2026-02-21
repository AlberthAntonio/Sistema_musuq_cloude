"""
Esquemas Pydantic para Docente.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocenteBase(BaseModel):
    """Esquema base de docente."""
    nombres: str
    apellidos: str
    dni: Optional[str] = None
    celular: Optional[str] = None
    email: Optional[str] = None
    especialidad: Optional[str] = None


class DocenteCreate(DocenteBase):
    """Esquema para crear docente."""
    pass


class DocenteUpdate(BaseModel):
    """Esquema para actualizar docente."""
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    dni: Optional[str] = None
    celular: Optional[str] = None
    email: Optional[str] = None
    especialidad: Optional[str] = None
    activo: Optional[bool] = None


class DocenteResponse(DocenteBase):
    """Esquema de respuesta de docente."""
    id: int
    activo: bool
    fecha_creacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DocenteResumen(BaseModel):
    """Esquema resumido para listados."""
    id: int
    nombre_completo: str
    especialidad: Optional[str] = None
    activo: bool
    
    class Config:
        from_attributes = True
