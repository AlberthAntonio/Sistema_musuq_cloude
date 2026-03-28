"""
Esquemas Pydantic para Horario.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HorarioBase(BaseModel):
    """Esquema base de horario de clases.
    
    NOTA: 'turno' indica el turno del BLOQUE DE CLASE (MAÑANA o TARDE).
    No confundir con el campo 'horario' del alumno (MATUTINO/VESPERTINO/DOBLE HORARIO).
    """
    curso_id: int
    docente_id: Optional[int] = None
    grupo: str
    periodo: str = "2026-I"
    dia_semana: int  # 1=Lunes...6=Sábado
    hora_inicio: str
    hora_fin: str
    aula: Optional[str] = None
    aula_id: Optional[int] = None  # FK a la tabla aulas
    turno: Optional[str] = None  # MAÑANA o TARDE (turno del bloque de clase)


class HorarioCreate(HorarioBase):
    """Esquema para crear horario."""
    pass


class HorarioUpdate(BaseModel):
    """Esquema para actualizar horario."""
    curso_id: Optional[int] = None
    docente_id: Optional[int] = None
    grupo: Optional[str] = None
    periodo: Optional[str] = None
    dia_semana: Optional[int] = None
    hora_inicio: Optional[str] = None
    hora_fin: Optional[str] = None
    aula: Optional[str] = None
    aula_id: Optional[int] = None  # FK a la tabla aulas
    turno: Optional[str] = None  # MAÑANA o TARDE (turno del bloque de clase)
    activo: Optional[bool] = None


class HorarioResponse(HorarioBase):
    """Esquema de respuesta de horario."""
    id: int
    activo: bool
    dia_nombre: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class HorarioCompleto(HorarioResponse):
    """Esquema con información completa de curso y docente."""
    curso_nombre: Optional[str] = None
    docente_nombre: Optional[str] = None
