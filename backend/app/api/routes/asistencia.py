"""
Rutas para gestión de asistencia - Optimizado.
- Filtros obligatorios en listados de alto volumen
- Paginación con X-Total-Count header
- Schemas reducidos para listados
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.asistencia import (
    AsistenciaCreate, AsistenciaResponse, AsistenciaUpdate,
    AsistenciaListItem,
    AsistenciaMasiva, AsistenciaReporte
)
from app.dependencies import get_asistencia_service
from app.services.asistencia_service import AsistenciaService
from app.api.routes.auth import get_current_user, require_role
from app.core.config import settings
from app.core.pagination import build_paginated_payload

router = APIRouter()


@router.get("/", response_model=List[AsistenciaListItem])
async def listar_asistencias(
    request: Request,
    response: Response,
    fecha: Optional[date] = Query(None, description="Filtrar por fecha exacta"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio del rango (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin del rango (YYYY-MM-DD)"),
    alumno_id: Optional[int] = Query(None, description="Filtrar por alumno"),
    grupo: Optional[str] = Query(None, description="Filtrar por grupo"),
    turno: Optional[str] = Query(None, description="Filtrar por turno (MAÑANA, TARDE)"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (Puntual, Tarde, Falta)"),
    periodo_id: Optional[int] = Query(None, description="Filtrar por periodo académico"),
    skip: int = Query(0, ge=0, description="Offset de paginación"),
    limit: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Límite de registros por página"
    ),
    format: Optional[str] = Query(None, description="Usar 'paginated' para respuesta con data/meta"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    asistencia_service: AsistenciaService = Depends(get_asistencia_service)
):
    """
    Listar asistencias con filtros.
    Requiere al menos un filtro de contexto: periodo_id, fecha, rango de fechas o alumno_id.
    """
    if settings.STRICT_HEAVY_QUERY_FILTERS and not (periodo_id or fecha or fecha_inicio or fecha_fin or alumno_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Consulta muy amplia. Enviar al menos periodo_id, fecha exacta, rango de fechas o alumno_id."
        )

    results = asistencia_service.listar(
        db, skip, limit, fecha, alumno_id, grupo, turno, estado, fecha_inicio, fecha_fin, periodo_id
    )
    total_count = asistencia_service.contar(
        db,
        fecha=fecha,
        alumno_id=alumno_id,
        grupo=grupo,
        turno=turno,
        estado=estado,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        periodo_id=periodo_id,
    )
    has_next = (skip + limit) < total_count
    response.headers["X-Total-Count"] = str(total_count)
    response.headers["X-Has-Next"] = str(has_next).lower()

    if format == "paginated":
        payload = build_paginated_payload(
            data=results,
            limit=limit,
            offset=skip,
            total=total_count,
            request_id=getattr(request.state, "request_id", None),
        )
        return JSONResponse(
            content=jsonable_encoder(payload),
            headers={
                "X-Total-Count": str(total_count),
                "X-Has-Next": str(has_next).lower(),
            },
        )
    return results


@router.post("/", response_model=AsistenciaResponse, status_code=status.HTTP_201_CREATED)
async def registrar_asistencia(
    asistencia: AsistenciaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    asistencia_service: AsistenciaService = Depends(get_asistencia_service)
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
    current_user: Usuario = Depends(require_role("admin", "secretaria", "docente")),
    asistencia_service: AsistenciaService = Depends(get_asistencia_service)
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
    current_user: Usuario = Depends(get_current_user),
    asistencia_service: AsistenciaService = Depends(get_asistencia_service)
):
    """Obtener asistencias del día de hoy."""
    return asistencia_service.obtener_hoy(db, grupo, turno)


@router.get("/reporte/fecha/{fecha_reporte}")
async def reporte_por_fecha(
    fecha_reporte: date,
    grupo: Optional[str] = None,
    turno: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    asistencia_service: AsistenciaService = Depends(get_asistencia_service)
):
    """Reporte de asistencia por fecha."""
    return asistencia_service.reporte_por_fecha(db, fecha_reporte, grupo, turno)


@router.get("/reporte/alumno/{alumno_id}", response_model=AsistenciaReporte)
async def reporte_alumno(
    alumno_id: int,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    periodo_id: Optional[int] = Query(None, description="Filtrar por periodo académico"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    asistencia_service: AsistenciaService = Depends(get_asistencia_service)
):
    """Reporte de asistencia de un alumno."""
    try:
        return asistencia_service.reporte_alumno(db, alumno_id, fecha_inicio, fecha_fin, periodo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{asistencia_id}", response_model=AsistenciaResponse)
async def actualizar_asistencia(
    asistencia_id: int,
    asistencia_update: AsistenciaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    asistencia_service: AsistenciaService = Depends(get_asistencia_service)
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
    current_user: Usuario = Depends(require_role("admin")),
    asistencia_service: AsistenciaService = Depends(get_asistencia_service)
):
    """Eliminar registro de asistencia (solo admin)."""
    try:
        asistencia_service.eliminar(db, asistencia_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
