"""
Rutas CRUD para horarios - Usando capa de servicios.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.horario import HorarioCreate, HorarioUpdate, HorarioResponse
from app.services.horario_service import horario_service
from app.api.routes.auth import get_current_user, require_role

router = APIRouter()


@router.get("/", response_model=List[HorarioResponse])
async def listar_horarios(
    grupo: Optional[str] = Query(None, description="Filtrar por grupo (A, B, C, D)"),
    dia_semana: Optional[int] = Query(None, ge=1, le=6, description="Día (1=Lunes...6=Sábado)"),
    curso_id: Optional[int] = Query(None, description="Filtrar por curso"),
    docente_id: Optional[int] = Query(None, description="Filtrar por docente"),
    activo: Optional[bool] = Query(True, description="Filtrar por estado activo"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar horarios con filtros opcionales."""
    return horario_service.listar(db, grupo, dia_semana, curso_id, docente_id, activo)


@router.post("/", response_model=HorarioResponse, status_code=status.HTTP_201_CREATED)
async def crear_horario(
    horario: HorarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Crear nuevo horario (solo admin)."""
    try:
        return horario_service.crear(db, horario)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/por-grupo/{grupo}")
async def horarios_por_grupo(
    grupo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener horarios de un grupo con información completa."""
    return horario_service.obtener_por_grupo(db, grupo)


@router.get("/por-docente/{docente_id}", response_model=List[HorarioResponse])
async def horarios_por_docente(
    docente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener horarios de un docente."""
    return horario_service.obtener_por_docente(db, docente_id)


@router.get("/{horario_id}", response_model=HorarioResponse)
async def obtener_horario(
    horario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener horario por ID."""
    horario = horario_service.obtener_por_id(db, horario_id)
    if not horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    return horario


@router.put("/{horario_id}", response_model=HorarioResponse)
async def actualizar_horario(
    horario_id: int,
    horario_update: HorarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Actualizar horario (solo admin)."""
    try:
        return horario_service.actualizar(db, horario_id, horario_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{horario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_horario(
    horario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Eliminar horario (solo admin)."""
    try:
        horario_service.eliminar(db, horario_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{horario_id}/desactivar", response_model=HorarioResponse)
async def desactivar_horario(
    horario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Desactivar horario (solo admin)."""
    try:
        return horario_service.desactivar(db, horario_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
