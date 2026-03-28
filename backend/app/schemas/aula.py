"""
Esquemas Pydantic para Aulas.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AulaHorarioCreate(BaseModel):
    """Bloque de horario a crear dentro de un aula."""
    curso_id: int
    docente_id: Optional[int] = None
    grupo: str
    periodo: str = "2026-I"
    dia_semana: int
    hora_inicio: str
    hora_fin: str
    turno: Optional[str] = None


class AulaBase(BaseModel):
    """Esquema base de aula."""
    nombre: str
    modalidad: str = "COLEGIO"
    descripcion: Optional[str] = None


class AulaCreate(AulaBase):
    """Esquema para crear aula y asignaciones."""
    grupos: List[str] = Field(default_factory=list)
    cursos_ids: List[int] = Field(default_factory=list)
    horarios: List[AulaHorarioCreate] = Field(default_factory=list)


class AulaUpdate(BaseModel):
    """Esquema para actualizar aula."""
    nombre: Optional[str] = None
    modalidad: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None
    grupos: Optional[List[str]] = None
    cursos_ids: Optional[List[int]] = None


class AulaResponse(AulaBase):
    """Esquema de respuesta de aula."""
    id: int
    activo: bool
    fecha_creacion: Optional[datetime] = None
    grupos: List[str] = Field(default_factory=list)
    cursos_ids: List[int] = Field(default_factory=list)

    class Config:
        from_attributes = True
