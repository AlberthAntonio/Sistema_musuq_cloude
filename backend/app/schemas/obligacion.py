"""
Esquemas Pydantic para Obligación de Pago.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class ObligacionBase(BaseModel):
    """Esquema base de obligación de pago."""
    matricula_id: int
    concepto: str
    monto_total: float
    fecha_vencimiento: Optional[date] = None


class ObligacionCreate(ObligacionBase):
    """Esquema para crear obligación de pago."""
    pass


class ObligacionUpdate(BaseModel):
    """Esquema para actualizar obligación de pago."""
    concepto: Optional[str] = None
    monto_total: Optional[float] = None
    fecha_vencimiento: Optional[date] = None


class ObligacionResponse(ObligacionBase):
    """Esquema de respuesta de obligación de pago."""
    id: int
    monto_pagado: float
    estado: str  # 'pendiente', 'parcial', 'pagado'
    saldo_pendiente: float
    creado_por: Optional[int] = None
    fecha_registro: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ObligacionConDetalle(ObligacionResponse):
    """Esquema con datos de la matrícula y alumno."""
    alumno_nombre: Optional[str] = None
    alumno_dni: Optional[str] = None
    codigo_matricula: Optional[str] = None
