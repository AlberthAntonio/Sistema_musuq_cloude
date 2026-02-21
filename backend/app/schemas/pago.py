"""
Esquemas Pydantic para Pago.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class PagoBase(BaseModel):
    """Esquema base de pago."""
    alumno_id: int
    monto: float
    fecha: date
    concepto: Optional[str] = None


class PagoCreate(PagoBase):
    """Esquema para crear pago."""
    pass


class PagoUpdate(BaseModel):
    """Esquema para actualizar pago."""
    monto: Optional[float] = None
    fecha: Optional[date] = None
    concepto: Optional[str] = None


class PagoResponse(PagoBase):
    """Esquema de respuesta de pago."""
    id: int
    fecha_registro: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PagoConAlumno(PagoResponse):
    """Esquema con información del alumno."""
    alumno_nombre: Optional[str] = None
    alumno_codigo: Optional[str] = None


class ResumenPagosAlumno(BaseModel):
    """Esquema de resumen de pagos de un alumno."""
    alumno_id: int
    total_pagado: float
    cantidad_pagos: int
    ultimo_pago: Optional[date] = None
