"""
Esquemas Pydantic para Lista Guardada.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ListaBase(BaseModel):
    """Esquema base de lista."""
    nombre: str
    descripcion: Optional[str] = None


class ListaCreate(ListaBase):
    """Esquema para crear lista."""
    alumno_ids: Optional[List[int]] = []


class ListaUpdate(BaseModel):
    """Esquema para actualizar lista."""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None


class ListaAddAlumnos(BaseModel):
    """Esquema para agregar alumnos a lista."""
    alumno_ids: List[int]


class ListaResponse(ListaBase):
    """Esquema de respuesta de lista."""
    id: int
    fecha_creacion: Optional[datetime] = None
    cantidad_alumnos: Optional[int] = 0
    
    class Config:
        from_attributes = True


class ListaConAlumnos(ListaResponse):
    """Esquema con lista de alumnos."""
    alumnos: List[dict] = []  # Lista de alumnos resumidos
