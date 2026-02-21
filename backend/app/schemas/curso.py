"""
Esquemas Pydantic para Curso y Malla Curricular.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ========== CURSO ==========

class CursoBase(BaseModel):
    """Esquema base de curso."""
    nombre: str
    descripcion: Optional[str] = None


class CursoCreate(CursoBase):
    """Esquema para crear curso."""
    pass


class CursoUpdate(BaseModel):
    """Esquema para actualizar curso."""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None


class CursoResponse(CursoBase):
    """Esquema de respuesta de curso."""
    id: int
    fecha_creacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ========== MALLA CURRICULAR ==========

class MallaCurricularBase(BaseModel):
    """Esquema base de malla curricular."""
    grupo: str
    curso_id: int


class MallaCurricularCreate(MallaCurricularBase):
    """Esquema para crear asignación de malla."""
    pass


class MallaCurricularResponse(MallaCurricularBase):
    """Esquema de respuesta de malla curricular."""
    id: int
    curso: Optional[CursoResponse] = None
    
    class Config:
        from_attributes = True
