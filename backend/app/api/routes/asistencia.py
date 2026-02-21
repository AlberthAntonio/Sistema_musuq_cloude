"""
Rutas para gestión de asistencia - Usando capa de servicios.
Estados: Puntual, Tarde, Falta
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.asistencia import (
    AsistenciaCreate, AsistenciaResponse, AsistenciaUpdate, 
    AsistenciaMasiva, AsistenciaReporte
)
from app.services.asistencia_service import asistencia_service
from app.api.routes.auth import get_current_user, require_role

router = APIRouter()


@router.get("/", response_model=List[AsistenciaResponse])
async def listar_asistencias(
    fecha: Optional[date] = Query(None, description="Filtrar por fecha exacta"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio del rango (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin del rango (YYYY-MM-DD)"),
    alumno_id: Optional[int] = Query(None, description="Filtrar por alumno"),
    grupo: Optional[str] = Query(None, description="Filtrar por grupo"),
    turno: Optional[str] = Query(None, description="Filtrar por turno (MAÑANA, TARDE)"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (Puntual, Tarde, Falta)"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar asistencias con filtros opcionales. Soporta fecha exacta o rango fecha_inicio/fecha_fin."""
    return asistencia_service.listar(
        db, skip, limit, fecha, alumno_id, grupo, turno, estado, fecha_inicio, fecha_fin
    )


@router.post("/", response_model=AsistenciaResponse, status_code=status.HTTP_201_CREATED)
async def registrar_asistencia(
    asistencia: AsistenciaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Registrar asistencia de un alumno."""
    try:
        return asistencia_service.registrar(db, asistencia, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/masivo", status_code=status.HTTP_201_CREATED)
async def registrar_asistencia_masiva(
    datos: AsistenciaMasiva,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin", "secretaria", "docente"))
):
    """Registrar asistencia de múltiples alumnos a la vez."""
    return asistencia_service.registrar_masivo(
        db, datos.fecha, datos.turno, datos.registros, current_user.id
    )


@router.get("/hoy", response_model=List[AsistenciaResponse])
async def asistencias_hoy(
    grupo: Optional[str] = None,
    turno: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener asistencias del día de hoy."""
    return asistencia_service.obtener_hoy(db, grupo, turno)


@router.get("/reporte/fecha/{fecha_reporte}")
async def reporte_por_fecha(
    fecha_reporte: date,
    grupo: Optional[str] = None,
    turno: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Reporte de asistencia por fecha."""
    return asistencia_service.reporte_por_fecha(db, fecha_reporte, grupo, turno)


@router.get("/reporte/alumno/{alumno_id}", response_model=AsistenciaReporte)
async def reporte_alumno(
    alumno_id: int,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Reporte de asistencia de un alumno."""
    try:
        return asistencia_service.reporte_alumno(db, alumno_id, fecha_inicio, fecha_fin)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{asistencia_id}", response_model=AsistenciaResponse)
async def actualizar_asistencia(
    asistencia_id: int,
    asistencia_update: AsistenciaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar registro de asistencia."""
    try:
        return asistencia_service.actualizar(db, asistencia_id, asistencia_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{asistencia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_asistencia(
    asistencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Eliminar registro de asistencia (solo admin)."""
    try:
        asistencia_service.eliminar(db, asistencia_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
