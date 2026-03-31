"""
Rutas CRUD para aulas.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.aula import AulaCreate, AulaUpdate, AulaResponse
from app.services.aula_service import aula_service
from app.api.routes.auth import get_current_user, require_role

router = APIRouter()


@router.get("/", response_model=List[AulaResponse])
async def listar_aulas(
    modalidad: Optional[str] = Query(None, description="Filtrar por modalidad de aula"),
    activo: Optional[bool] = Query(True, description="Filtrar por estado activo"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar aulas con filtros opcionales."""
    return aula_service.listar(db, modalidad, activo)


@router.post("/", response_model=AulaResponse, status_code=status.HTTP_201_CREATED)
async def crear_aula(
    aula: AulaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Crear aula con grupos, cursos y horarios opcionales (solo admin)."""
    try:
        return aula_service.crear(db, aula)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{aula_id}", response_model=AulaResponse)
async def obtener_aula(
    aula_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener aula por ID."""
    aula = aula_service.obtener_por_id(db, aula_id)
    if not aula:
        raise HTTPException(status_code=404, detail="Aula no encontrada")
    return aula


@router.get("/{aula_id}/horarios")
async def obtener_horarios_de_aula(
    aula_id: int,
    response: Response,
    periodo: Optional[str] = Query(None, description="Filtrar por periodo, ej. 2026-I"),
    grupo: Optional[str] = Query(None, description="Filtrar por grupo"),
    turno: Optional[str] = Query(None, description="Filtrar por turno"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener bloques horarios asociados al aula usando la columna horarios.aula."""
    try:
        horarios, mode, reason = aula_service.obtener_horarios_aula_con_modo(
            db,
            aula_id,
            periodo,
            grupo,
            turno,
        )
        response.headers["X-Horarios-Mode"] = mode
        response.headers["X-Horarios-Rollout-Reason"] = reason
        return horarios
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{aula_id}", response_model=AulaResponse)
async def actualizar_aula(
    aula_id: int,
    aula_update: AulaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Actualizar aula y asignaciones (solo admin)."""
    try:
        return aula_service.actualizar(db, aula_id, aula_update)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{aula_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_aula(
    aula_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Eliminar aula (solo admin)."""
    try:
        aula_service.eliminar(db, aula_id)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
