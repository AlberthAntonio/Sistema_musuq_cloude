"""
Esquemas Pydantic para Sesión de Examen.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class SesionBase(BaseModel):
    """Esquema base de sesión."""
    fecha: date
    nombre: str
    estado: str = "Abierto"


class SesionCreate(SesionBase):
    """Esquema para crear sesión."""
    pass


class SesionUpdate(BaseModel):
    """Esquema para actualizar sesión."""
    fecha: Optional[date] = None
    nombre: Optional[str] = None
    estado: Optional[str] = None


class SesionResponse(SesionBase):
    """Esquema de respuesta de sesión."""
    id: int
    fecha_creacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SesionConNotas(SesionResponse):
    """Esquema con lista de notas."""
    notas: List[dict] = []
