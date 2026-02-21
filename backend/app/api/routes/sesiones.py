"""
Rutas CRUD para sesiones de examen.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.sesion import SesionCreate, SesionUpdate, SesionResponse
from app.services.sesion_service import sesion_service
from app.api.routes.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[SesionResponse])
async def listar_sesiones(
    estado: Optional[str] = Query(None, description="Filtrar por estado (Abierto, Cerrado)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar sesiones de examen."""
    return sesion_service.listar(db, estado)


@router.post("/", response_model=SesionResponse, status_code=status.HTTP_201_CREATED)
async def crear_sesion(
    sesion: SesionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear nueva sesión de examen."""
    return sesion_service.crear(db, sesion)


@router.get("/{sesion_id}")
async def obtener_sesion(
    sesion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener sesión con sus notas."""
    sesion = sesion_service.obtener_con_notas(db, sesion_id)
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return sesion


@router.put("/{sesion_id}", response_model=SesionResponse)
async def actualizar_sesion(
    sesion_id: int,
    sesion_update: SesionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar sesión."""
    try:
        return sesion_service.actualizar(db, sesion_id, sesion_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{sesion_id}/cerrar", response_model=SesionResponse)
async def cerrar_sesion(
    sesion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Cerrar una sesión de examen."""
    try:
        return sesion_service.cerrar_sesion(db, sesion_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{sesion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_sesion(
    sesion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar sesión."""
    try:
        sesion_service.eliminar(db, sesion_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
