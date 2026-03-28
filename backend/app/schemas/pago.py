"""
Esquemas Pydantic para Pago.
Ahora vinculado a ObligacionPago en lugar de Alumno directamente.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class PagoBase(BaseModel):
    """Esquema base de pago."""
    obligacion_id: int
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
    creado_por: Optional[int] = None
    fecha_registro: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PagoConDetalle(PagoResponse):
    """Esquema con información de la obligación y el alumno."""
    obligacion_concepto: Optional[str] = None
    alumno_nombre: Optional[str] = None
    alumno_dni: Optional[str] = None


class ResumenPagosMatricula(BaseModel):
    """Esquema de resumen de pagos de una matrícula."""
    matricula_id: int
    codigo_matricula: str
    total_obligaciones: float
    total_pagado: float
    saldo_pendiente: float
    cantidad_pagos: int
    ultimo_pago: Optional[date] = None
