"""
Esquemas Pydantic para Evento de Calendario.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class EventoBase(BaseModel):
    """Esquema base de evento."""
    titulo: str
    descripcion: Optional[str] = None
    fecha: date
    hora_inicio: Optional[str] = None
    hora_fin: Optional[str] = None
    tipo: Optional[str] = None  # examen, reunion, feriado, evento
    grupo: Optional[str] = None  # A, B, C, null=todos


class EventoCreate(EventoBase):
    """Esquema para crear evento."""
    publico: bool = True


class EventoUpdate(BaseModel):
    """Esquema para actualizar evento."""
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    fecha: Optional[date] = None
    hora_inicio: Optional[str] = None
    hora_fin: Optional[str] = None
    tipo: Optional[str] = None
    grupo: Optional[str] = None
    publico: Optional[bool] = None
    activo: Optional[bool] = None


class EventoResponse(EventoBase):
    """Esquema de respuesta de evento."""
    id: int
    publico: bool
    activo: bool
    fecha_creacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True
