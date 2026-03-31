"""
Esquemas Pydantic para plantillas de horario.
"""
from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class PlantillaHorarioBase(BaseModel):
    aula_id: int
    grupo: str
    periodo: str
    turno: str
    version: int = 1


class PlantillaHorarioCreate(PlantillaHorarioBase):
    activo: bool = True


class PlantillaHorarioUpdate(BaseModel):
    aula_id: Optional[int] = None
    grupo: Optional[str] = None
    periodo: Optional[str] = None
    turno: Optional[str] = None
    version: Optional[int] = None
    activo: Optional[bool] = None


class PlantillaHorarioResponse(PlantillaHorarioBase):
    id: int
    activo: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PlantillaBloqueBase(BaseModel):
    dia_semana: int = Field(..., ge=1, le=6)
    hora_inicio: str = Field(..., min_length=5, max_length=5)
    hora_fin: str = Field(..., min_length=5, max_length=5)
    tipo_bloque: Literal["CLASE", "RECREO", "LIBRE"]
    etiqueta: Optional[str] = None
    orden_visual: Optional[int] = None


class PlantillaBloqueCreate(PlantillaBloqueBase):
    activo: bool = True


class PlantillaBloqueUpdate(BaseModel):
    dia_semana: Optional[int] = Field(None, ge=1, le=6)
    hora_inicio: Optional[str] = Field(None, min_length=5, max_length=5)
    hora_fin: Optional[str] = Field(None, min_length=5, max_length=5)
    tipo_bloque: Optional[Literal["CLASE", "RECREO", "LIBRE"]] = None
    etiqueta: Optional[str] = None
    orden_visual: Optional[int] = None
    activo: Optional[bool] = None


class PlantillaBloqueResponse(PlantillaBloqueBase):
    id: int
    plantilla_id: int
    activo: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PlantillaBloqueBatchItem(BaseModel):
    id: Optional[int] = None
    dia_semana: int = Field(..., ge=1, le=6)
    hora_inicio: str = Field(..., min_length=5, max_length=5)
    hora_fin: str = Field(..., min_length=5, max_length=5)
    tipo_bloque: Literal["CLASE", "RECREO", "LIBRE"]
    etiqueta: Optional[str] = None
    orden_visual: Optional[int] = None
    activo: bool = True


class PlantillaBloqueBatchUpsertRequest(BaseModel):
    bloques: List[PlantillaBloqueBatchItem]
    eliminar_no_incluidos: bool = False


class PlantillaBloqueBatchUpsertResponse(BaseModel):
    plantilla_id: int
    creados: int
    actualizados: int
    eliminados: int
    bloques: List[PlantillaBloqueResponse]


class GrillaBloqueItem(BaseModel):
    bloque_id: int
    dia_semana: int
    hora_inicio: str
    hora_fin: str
    tipo_bloque: str
    etiqueta: Optional[str] = None
    orden_visual: Optional[int] = None
    horario_id: Optional[int] = None
    curso_id: Optional[int] = None
    curso_nombre: Optional[str] = None
    docente_id: Optional[int] = None
    docente_nombre: Optional[str] = None


class PlantillaGrillaFinalResponse(BaseModel):
    plantilla_id: Optional[int] = None
    aula_id: int
    grupo: str
    periodo: str
    turno: str
    bloques_por_dia: Dict[str, List[GrillaBloqueItem]]
