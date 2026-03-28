"""
Rutas CRUD para periodos académicos.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.periodo import PeriodoCreate, PeriodoUpdate, PeriodoResponse
from app.services.periodo_service import periodo_service
from app.api.routes.auth import get_current_user, require_role, verificar_no_auxiliar

router = APIRouter()


@router.get("/", response_model=List[PeriodoResponse])
async def listar_periodos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todos los periodos académicos."""
    return periodo_service.listar(db)


@router.post("/", response_model=PeriodoResponse, status_code=status.HTTP_201_CREATED)
async def crear_periodo(
    periodo: PeriodoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Crear nuevo periodo académico (solo admin)."""
    try:
        return periodo_service.crear(db, periodo, usuario_actual_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/activo", response_model=PeriodoResponse)
async def obtener_periodo_activo(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener el periodo académico activo."""
    periodo = periodo_service.obtener_activo(db)
    if not periodo:
        raise HTTPException(status_code=404, detail="No hay periodo activo")
    return periodo


@router.get("/{periodo_id}", response_model=PeriodoResponse)
async def obtener_periodo(
    periodo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener periodo por ID."""
    periodo = periodo_service.obtener_por_id(db, periodo_id)
    if not periodo:
        raise HTTPException(status_code=404, detail="Periodo no encontrado")
    return periodo


@router.put("/{periodo_id}", response_model=PeriodoResponse)
async def actualizar_periodo(
    periodo_id: int,
    periodo_update: PeriodoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Actualizar periodo académico."""
    try:
        return periodo_service.actualizar(db, periodo_id, periodo_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{periodo_id}/cerrar", response_model=PeriodoResponse)
async def cerrar_periodo(
    periodo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Cerrar un periodo académico (solo admin)."""
    try:
        return periodo_service.cerrar(db, periodo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{periodo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_periodo(
    periodo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Eliminar periodo académico (solo admin)."""
    try:
        periodo_service.eliminar(db, periodo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
