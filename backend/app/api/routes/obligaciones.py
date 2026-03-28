"""
Rutas CRUD para obligaciones de pago.
Con RBAC: AUXILIAR no puede crear/actualizar/eliminar obligaciones.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.obligacion import (
    ObligacionCreate, ObligacionUpdate, ObligacionResponse
)
from app.services.obligacion_service import obligacion_service
from app.api.routes.auth import get_current_user, verificar_no_auxiliar

router = APIRouter()


@router.get("/", response_model=List[ObligacionResponse])
async def listar_obligaciones(
    matricula_id: Optional[int] = Query(None, description="Filtrar por matrícula"),
    periodo_id: Optional[int] = Query(None, description="Filtrar por periodo"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar obligaciones de pago con filtros opcionales."""
    return obligacion_service.listar(db, matricula_id, periodo_id, estado, skip, limit)


@router.post("/", response_model=ObligacionResponse, status_code=status.HTTP_201_CREATED)
async def crear_obligacion(
    obligacion: ObligacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_no_auxiliar)
):
    """Crear nueva obligación de pago. Bloqueado para AUXILIAR."""
    try:
        return obligacion_service.crear(db, obligacion, usuario_actual_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{obligacion_id}", response_model=ObligacionResponse)
async def obtener_obligacion(
    obligacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener obligación por ID."""
    obligacion = obligacion_service.obtener_por_id(db, obligacion_id)
    if not obligacion:
        raise HTTPException(status_code=404, detail="Obligación no encontrada")
    return obligacion


@router.put("/{obligacion_id}", response_model=ObligacionResponse)
async def actualizar_obligacion(
    obligacion_id: int,
    obligacion_update: ObligacionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_no_auxiliar)
):
    """Actualizar obligación de pago. Bloqueado para AUXILIAR."""
    try:
        return obligacion_service.actualizar(db, obligacion_id, obligacion_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{obligacion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_obligacion(
    obligacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_no_auxiliar)
):
    """Eliminar obligación de pago. Bloqueado para AUXILIAR."""
    try:
        obligacion_service.eliminar(db, obligacion_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
