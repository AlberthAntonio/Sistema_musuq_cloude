"""
Rutas CRUD para eventos de calendario.
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.evento import EventoCreate, EventoUpdate, EventoResponse
from app.services.evento_service import evento_service
from app.api.routes.auth import get_current_user, require_role

router = APIRouter()


@router.get("/", response_model=List[EventoResponse])
async def listar_eventos(
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    tipo: Optional[str] = Query(None),
    grupo: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar eventos con filtros opcionales."""
    return evento_service.listar(db, fecha_desde, fecha_hasta, tipo, grupo)


@router.post("/", response_model=EventoResponse, status_code=status.HTTP_201_CREATED)
async def crear_evento(
    evento: EventoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Crear nuevo evento (solo admin)."""
    return evento_service.crear(db, evento)


@router.get("/{evento_id}", response_model=EventoResponse)
async def obtener_evento(
    evento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener evento por ID."""
    evento = evento_service.obtener_por_id(db, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return evento


@router.put("/{evento_id}", response_model=EventoResponse)
async def actualizar_evento(
    evento_id: int,
    evento_update: EventoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Actualizar evento (solo admin)."""
    try:
        return evento_service.actualizar(db, evento_id, evento_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{evento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_evento(
    evento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Eliminar evento (solo admin)."""
    try:
        evento_service.eliminar(db, evento_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
