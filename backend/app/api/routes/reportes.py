"""
Rutas de Reportes Consolidados.
Endpoints optimizados que reemplazan los patrones N×requests del cliente desktop.
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.services.reporte_service import reporte_service
from app.api.routes.auth import get_current_user

router = APIRouter()


@router.get("/deudores")
async def reporte_deudores(
    periodo_id: Optional[int] = Query(None, description="Filtrar por periodo académico"),
    grupo: Optional[str] = Query(None, description="Filtrar por grupo"),
    modalidad: Optional[str] = Query(None, description="Filtrar por modalidad"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Lista alumnos con saldo pendiente > 0.
    Una sola consulta SQL — reemplaza el patrón N×2 requests del desktop.
    """
    return reporte_service.reporte_deudores(db, periodo_id=periodo_id, grupo=grupo, modalidad=modalidad)


@router.get("/tardanzas")
async def reporte_tardanzas(
    fecha_inicio: Optional[date] = Query(None, description="Desde esta fecha (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Hasta esta fecha (YYYY-MM-DD)"),
    grupo: Optional[str] = Query(None, description="Filtrar por grupo"),
    turno: Optional[str] = Query(None, description="Filtrar por turno (MAÑANA/TARDE)"),
    periodo_id: Optional[int] = Query(None, description="Filtrar por periodo"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Lista todos los registros de TARDANZA en el rango de fechas.
    Reemplaza el loop de 500-en-500 del controlador de tardanzas del desktop.
    """
    return reporte_service.reporte_tardanzas(
        db,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        grupo=grupo,
        turno=turno,
        periodo_id=periodo_id,
    )


@router.get("/asistencia")
async def reporte_asistencia_resumen(
    periodo_id: Optional[int] = Query(None, description="Filtrar por periodo"),
    grupo: Optional[str] = Query(None, description="Filtrar por grupo"),
    fecha_inicio: Optional[date] = Query(None, description="Desde esta fecha"),
    fecha_fin: Optional[date] = Query(None, description="Hasta esta fecha"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Resumen de asistencia por alumno: puntual / tardanza / falta + porcentaje.
    Una sola consulta SQL con GROUP BY.
    """
    return reporte_service.reporte_asistencia_resumen(
        db,
        periodo_id=periodo_id,
        grupo=grupo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )


@router.get("/estadisticas/{periodo_id}")
async def estadisticas_periodo(
    periodo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Resumen estadístico completo de un periodo académico:
    total matriculados, deuda/pagos globales, porcentaje de asistencia promedio.
    """
    try:
        return reporte_service.estadisticas_periodo(db, periodo_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
