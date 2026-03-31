"""
Rutas de Reportes Consolidados.
Endpoints optimizados que reemplazan los patrones N×requests del cliente desktop.
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.services.reporte_service import reporte_service
from app.api.routes.auth import get_current_user
from app.core.config import settings
from app.core.cache import cached
from app.services.job_manager import job_manager

router = APIRouter()

def _run_report_job(job_id: str, func, *args, **kwargs):
    """Ejecutor genérico para BackgroundTasks que enmascara los DB errors y libera la conexión."""
    job_manager.set_processing(job_id)
    try:
        from app.db import SessionLocal
        db = SessionLocal()
        try:
            # Reemplazar la 'db' original por la nueva si estaba en kwargs
            if 'db' in kwargs: kwargs['db'] = db
            else: args = (db, *args[1:])
            result = func(*args, **kwargs)
            job_manager.finish_job(job_id, result)
        finally:
            db.close()
    except Exception as e:
        import traceback
        job_manager.fail_job(job_id, f"{str(e)}\n{traceback.format_exc()}")


@router.get("/deudores")
async def reporte_deudores(
    periodo_id: Optional[int] = Query(None, description="Filtrar por periodo académico"),
    grupo: Optional[str] = Query(None, description="Filtrar por grupo"),
    modalidad: Optional[str] = Query(None, description="Filtrar por modalidad"),
    async_mode: bool = Query(False, description="Ejecutar en fondo devolviendo un Ticket ID"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Lista alumnos con saldo pendiente > 0.
    Una sola consulta SQL — reemplaza el patrón N×2 requests del desktop.
    """
    if settings.STRICT_HEAVY_QUERY_FILTERS and not (periodo_id or grupo or modalidad):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Consulta muy amplia. Enviar al menos periodo_id, grupo o modalidad."
        )
        
    if async_mode and background_tasks:
        job_id = job_manager.create_job()
        background_tasks.add_task(_run_report_job, job_id, reporte_service.reporte_deudores, db, periodo_id, grupo, modalidad)
        return {"job_id": job_id, "status": "pending", "message": "Report queued"}
    
    return reporte_service.reporte_deudores(db, periodo_id=periodo_id, grupo=grupo, modalidad=modalidad)


@router.get("/tardanzas")
async def reporte_tardanzas(
    fecha_inicio: Optional[date] = Query(None, description="Desde esta fecha (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Hasta esta fecha (YYYY-MM-DD)"),
    grupo: Optional[str] = Query(None, description="Filtrar por grupo"),
    turno: Optional[str] = Query(None, description="Filtrar por turno (MAÑANA/TARDE)"),
    periodo_id: Optional[int] = Query(None, description="Filtrar por periodo"),
    async_mode: bool = Query(False, description="Ejecutar en fondo devolviendo un Ticket ID"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Lista todos los registros de TARDANZA en el rango de fechas.
    Reemplaza el loop de 500-en-500 del controlador de tardanzas del desktop.
    """
    if settings.STRICT_HEAVY_QUERY_FILTERS and not (periodo_id or (fecha_inicio and fecha_fin) or grupo):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Consulta muy amplia. Enviar al menos periodo_id, rango de fechas o grupo."
        )
        
    if async_mode and background_tasks:
        job_id = job_manager.create_job()
        background_tasks.add_task(_run_report_job, job_id, reporte_service.reporte_tardanzas, db, fecha_inicio, fecha_fin, grupo, turno, periodo_id)
        return {"job_id": job_id, "status": "pending", "message": "Report queued"}

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
    mes: Optional[int] = Query(None, ge=1, le=12, description="Filtrar por mes (1-12)"),
    async_mode: bool = Query(False, description="Ejecutar en fondo devolviendo un Ticket ID"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Resumen de asistencia por alumno: puntual / tardanza / falta + porcentaje.
    Una sola consulta SQL con GROUP BY.
    """
    if settings.STRICT_HEAVY_QUERY_FILTERS and not (periodo_id or grupo or mes):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Consulta muy amplia. Enviar al menos periodo_id, grupo o mes."
        )
        
    if async_mode and background_tasks:
        job_id = job_manager.create_job()
        background_tasks.add_task(
            _run_report_job,
            job_id,
            reporte_service.reporte_asistencia_resumen,
            db,
            periodo_id,
            grupo,
            fecha_inicio,
            fecha_fin,
            mes,
        )
        return {"job_id": job_id, "status": "pending", "message": "Report queued"}

    return reporte_service.reporte_asistencia_resumen(
        db,
        periodo_id=periodo_id,
        grupo=grupo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        mes=mes,
    )


@router.get("/estadisticas/{periodo_id}")
@cached(ttl=300) # Cachear 5 minutos los datos estadísticos pesados por periodo
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

@router.get("/jobs/{job_id}/status")
async def check_job_status(job_id: str):
    """Obtiene el status de un reporte asincrónico en background."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado o expirado")
    
    response = {"job_id": job_id, "status": job["status"], "created_at": job["created_at"]}
    if job["error"]:
        response["error"] = job["error"]
        
    return response

@router.get("/jobs/{job_id}/download")
async def download_job_result(job_id: str):
    """Entrega los resultados si el job reportó 'done'."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado o ya expirado")
        
    if job["status"] != "done":
        raise HTTPException(status_code=400, detail=f"Job no está completado. Status actual: {job['status']}")
        
    return job["result"]
