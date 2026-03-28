"""
Esquemas Pydantic para Periodo Académico.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class PeriodoBase(BaseModel):
    """Esquema base de periodo académico."""
    nombre: str
    tipo: str  # 'colegio' o 'academia'
    fecha_inicio: date
    fecha_fin: date


class PeriodoCreate(PeriodoBase):
    """Esquema para crear periodo académico."""
    estado: Optional[str] = "activo"


class PeriodoUpdate(BaseModel):
    """Esquema para actualizar periodo académico."""
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    estado: Optional[str] = None  # 'activo', 'cerrado'


class PeriodoResponse(PeriodoBase):
    """Esquema de respuesta de periodo académico."""
    id: int
    estado: str
    creado_por: Optional[int] = None
    fecha_registro: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True
