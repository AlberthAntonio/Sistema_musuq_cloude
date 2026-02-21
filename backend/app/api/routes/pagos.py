"""
Rutas CRUD para pagos.
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.pago import PagoCreate, PagoUpdate, PagoResponse
from app.services.pago_service import pago_service
from app.api.routes.auth import get_current_user

router = APIRouter()


@router.get("/")
async def listar_pagos(
    alumno_id: Optional[int] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar pagos con filtros opcionales."""
    return pago_service.listar(db, alumno_id, fecha_desde, fecha_hasta)


@router.post("/", response_model=PagoResponse, status_code=status.HTTP_201_CREATED)
async def crear_pago(
    pago: PagoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Registrar nuevo pago."""
    try:
        return pago_service.crear(db, pago)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/resumen/{alumno_id}")
async def resumen_pagos_alumno(
    alumno_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener resumen de pagos de un alumno."""
    return pago_service.resumen_por_alumno(db, alumno_id)


@router.get("/{pago_id}", response_model=PagoResponse)
async def obtener_pago(
    pago_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener pago por ID."""
    pago = pago_service.obtener_por_id(db, pago_id)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago


@router.put("/{pago_id}", response_model=PagoResponse)
async def actualizar_pago(
    pago_id: int,
    pago_update: PagoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar pago."""
    try:
        return pago_service.actualizar(db, pago_id, pago_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{pago_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_pago(
    pago_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar pago."""
    try:
        pago_service.eliminar(db, pago_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
