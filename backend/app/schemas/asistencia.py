"""
Esquemas Pydantic para Asistencia - Adaptado del sistema original.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import date, time, datetime
from app.schemas.alumno import AlumnoResponse


class AsistenciaBase(BaseModel):
    """Esquema base de asistencia."""
    alumno_id: int
    fecha: date
    turno: str  # "MAÑANA", "TARDE"
    estado: str = "PUNTUAL"  # PUNTUAL, TARDANZA, INASISTENCIA
    observacion: Optional[str] = None
    # Multi-tenant: si se omite se usa el periodo activo
    periodo_id: Optional[int] = None


class AsistenciaCreate(AsistenciaBase):
    """Esquema para crear asistencia."""
    hora: Optional[time] = None
    alerta_turno: Optional[bool] = False


class AsistenciaUpdate(BaseModel):
    """Esquema para actualizar asistencia."""
    estado: Optional[str] = None
    hora: Optional[time] = None
    turno: Optional[str] = None
    alerta_turno: Optional[bool] = None
    observacion: Optional[str] = None


class AsistenciaResponse(AsistenciaBase):
    """Esquema de respuesta de asistencia."""
    id: int
    alumno: Optional[AlumnoResponse] = None
    hora: Optional[time] = None
    alerta_turno: bool = False
    registrado_por: Optional[int] = None
    periodo_id: Optional[int] = None
    fecha_registro: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AsistenciaMasiva(BaseModel):
    """Esquema para registro masivo de asistencia."""
    fecha: date
    turno: str
    registros: list[dict]  # [{"alumno_id": 1, "estado": "PUNTUAL"}, ...]


class AsistenciaReporte(BaseModel):
    """Esquema para reportes de asistencia."""
    alumno_id: int
    codigo_matricula: str
    nombre_completo: str
    total_puntual: int = 0
    total_tardanza: int = 0
    total_falta: int = 0
    porcentaje_asistencia: float = 0.0
