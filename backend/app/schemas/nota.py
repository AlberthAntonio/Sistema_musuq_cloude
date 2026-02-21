"""
Esquemas Pydantic para Nota.
"""
from pydantic import BaseModel
from typing import Optional


class NotaBase(BaseModel):
    """Esquema base de nota."""
    alumno_id: int
    sesion_id: int
    curso_nombre: str
    valor: float


class NotaCreate(NotaBase):
    """Esquema para crear nota."""
    pass


class NotaUpdate(BaseModel):
    """Esquema para actualizar nota."""
    curso_nombre: Optional[str] = None
    valor: Optional[float] = None


class NotaResponse(NotaBase):
    """Esquema de respuesta de nota."""
    id: int
    
    class Config:
        from_attributes = True


class NotasMasivas(BaseModel):
    """Esquema para registro masivo de notas."""
    sesion_id: int
    notas: list[dict]  # [{"alumno_id": 1, "curso_nombre": "Aritmética", "valor": 15.0}, ...]


class NotaConDetalle(NotaResponse):
    """Esquema con información del alumno y sesión."""
    alumno_nombre: Optional[str] = None
    sesion_nombre: Optional[str] = None
