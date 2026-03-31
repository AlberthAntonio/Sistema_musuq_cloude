"""
Rutas para plantillas de horario y bloques (fase 2).
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user, require_role
from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.plantilla_horario import (
    PlantillaBloqueBatchUpsertRequest,
    PlantillaBloqueBatchUpsertResponse,
    PlantillaBloqueCreate,
    PlantillaBloqueResponse,
    PlantillaBloqueUpdate,
    PlantillaGrillaFinalResponse,
    PlantillaHorarioCreate,
    PlantillaHorarioResponse,
    PlantillaHorarioUpdate,
)
from app.services.plantilla_horario_service import plantilla_horario_service

router = APIRouter()


def _status_por_error(message: str) -> int:
    msg = (message or "").lower()
    if "no encontrada" in msg or "no encontrado" in msg:
        return status.HTTP_404_NOT_FOUND
    return status.HTTP_400_BAD_REQUEST


@router.get("/plantillas-horario/grilla-final", response_model=PlantillaGrillaFinalResponse)
async def obtener_grilla_final(
    aula_id: int = Query(..., description="ID del aula"),
    grupo: str = Query(..., description="Grupo"),
    periodo: str = Query(..., description="Periodo académico"),
    turno: str = Query(..., description="Turno"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene grilla final dinámica por alcance aula+grupo+periodo+turno."""
    return plantilla_horario_service.obtener_grilla_final(db, aula_id, grupo, periodo, turno)


@router.get("/plantillas-horario/", response_model=List[PlantillaHorarioResponse])
async def listar_plantillas(
    aula_id: Optional[int] = Query(None),
    grupo: Optional[str] = Query(None),
    periodo: Optional[str] = Query(None),
    turno: Optional[str] = Query(None),
    activo: Optional[bool] = Query(True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return plantilla_horario_service.listar_plantillas(db, aula_id, grupo, periodo, turno, activo)


@router.post(
    "/plantillas-horario/",
    response_model=PlantillaHorarioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_plantilla(
    payload: PlantillaHorarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin")),
):
    try:
        return plantilla_horario_service.crear_plantilla(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=_status_por_error(str(e)), detail=str(e))


@router.put("/plantillas-horario/{plantilla_id}", response_model=PlantillaHorarioResponse)
async def actualizar_plantilla(
    plantilla_id: int,
    payload: PlantillaHorarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin")),
):
    try:
        return plantilla_horario_service.actualizar_plantilla(db, plantilla_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=_status_por_error(str(e)), detail=str(e))


@router.delete("/plantillas-horario/{plantilla_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_plantilla(
    plantilla_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin")),
):
    try:
        plantilla_horario_service.eliminar_plantilla(db, plantilla_id)
    except ValueError as e:
        raise HTTPException(status_code=_status_por_error(str(e)), detail=str(e))


@router.get("/plantillas-horario/{plantilla_id}/bloques", response_model=List[PlantillaBloqueResponse])
async def listar_bloques(
    plantilla_id: int,
    activo: Optional[bool] = Query(True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return plantilla_horario_service.listar_bloques(db, plantilla_id, activo)
    except ValueError as e:
        raise HTTPException(status_code=_status_por_error(str(e)), detail=str(e))


@router.post(
    "/plantillas-horario/{plantilla_id}/bloques",
    response_model=PlantillaBloqueResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_bloque(
    plantilla_id: int,
    payload: PlantillaBloqueCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin")),
):
    try:
        return plantilla_horario_service.crear_bloque(db, plantilla_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=_status_por_error(str(e)), detail=str(e))


@router.post(
    "/plantillas-horario/{plantilla_id}/bloques/batch-upsert",
    response_model=PlantillaBloqueBatchUpsertResponse,
)
async def batch_upsert_bloques(
    plantilla_id: int,
    payload: PlantillaBloqueBatchUpsertRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin")),
):
    try:
        return plantilla_horario_service.batch_upsert_bloques(
            db,
            plantilla_id=plantilla_id,
            bloques=payload.bloques,
            eliminar_no_incluidos=payload.eliminar_no_incluidos,
        )
    except ValueError as e:
        raise HTTPException(status_code=_status_por_error(str(e)), detail=str(e))


@router.put("/plantilla-bloques/{bloque_id}", response_model=PlantillaBloqueResponse)
async def actualizar_bloque(
    bloque_id: int,
    payload: PlantillaBloqueUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin")),
):
    try:
        return plantilla_horario_service.actualizar_bloque(db, bloque_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=_status_por_error(str(e)), detail=str(e))


@router.delete("/plantilla-bloques/{bloque_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_bloque(
    bloque_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin")),
):
    try:
        plantilla_horario_service.eliminar_bloque(db, bloque_id)
    except ValueError as e:
        raise HTTPException(status_code=_status_por_error(str(e)), detail=str(e))
