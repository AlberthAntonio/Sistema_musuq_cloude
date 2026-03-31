"""
Rutas CRUD para matrículas.
Con RBAC: AUXILIAR no puede crear/actualizar/eliminar matrículas.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.matricula import (
    MatriculaCreate, MatriculaUpdate, MatriculaResponse, MatriculaConAlumno, MatriculaListItem
)
from app.api.routes.auth import get_current_user, verificar_no_auxiliar
from app.dependencies import get_matricula_service
from app.services.matricula_service import MatriculaService
from app.core.config import settings
from app.core.pagination import build_paginated_payload

router = APIRouter()


@router.get("/", response_model=List[MatriculaListItem])
async def listar_matriculas(
    request: Request,
    response: Response,
    periodo_id: Optional[int] = Query(None, description="Filtrar por periodo académico"),
    alumno_id: Optional[int] = Query(None, description="Filtrar por alumno"),
    grupo: Optional[str] = Query(None, description="Filtrar por grupo"),
    estado: Optional[str] = Query("activo", description="Filtrar por estado"),
    skip: int = Query(0, ge=0, description="Offset de paginación"),
    limit: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Límite de registros por página"
    ),
    format: Optional[str] = Query(None, description="Usar 'paginated' para respuesta con data/meta"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    matricula_service: MatriculaService = Depends(get_matricula_service),
):
    """Listar matrículas con filtros opcionales."""
    results = matricula_service.listar(db, periodo_id, alumno_id, grupo, estado, skip, limit)
    total_count = matricula_service.contar(db, periodo_id, alumno_id, grupo, estado)
    has_next = (skip + limit) < total_count
    response.headers["X-Total-Count"] = str(total_count)
    response.headers["X-Has-Next"] = str(has_next).lower()

    if format == "paginated":
        payload = build_paginated_payload(
            data=results,
            limit=limit,
            offset=skip,
            total=total_count,
            request_id=getattr(request.state, "request_id", None),
        )
        return JSONResponse(
            content=jsonable_encoder(payload),
            headers={
                "X-Total-Count": str(total_count),
                "X-Has-Next": str(has_next).lower(),
            },
        )
    return results


@router.post("/", response_model=MatriculaResponse, status_code=status.HTTP_201_CREATED)
async def crear_matricula(
    matricula: MatriculaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_no_auxiliar),
    matricula_service: MatriculaService = Depends(get_matricula_service),
):
    """
    Crear matrícula. Registra periodo, grupo, modalidad.
    El alumno debe existir. No lo pueden usar auxiliares.
    """
    try:
        return matricula_service.crear(db, matricula, usuario_actual_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{matricula_id}", response_model=MatriculaConAlumno)
async def obtener_matricula(
    matricula_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    matricula_service: MatriculaService = Depends(get_matricula_service),
):
    """Obtener detalle de matrícula con datos del alumno."""
    matricula = matricula_service.obtener_por_id(db, matricula_id)
    if not matricula:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")
    return matricula


@router.get("/codigo/{codigo}", response_model=MatriculaResponse)
async def obtener_matricula_por_codigo(
    codigo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    matricula_service: MatriculaService = Depends(get_matricula_service),
):
    """Obtener matrícula buscando por su código exacto."""
    matricula = matricula_service.obtener_por_codigo(db, codigo)
    if not matricula:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")
    return matricula


@router.put("/{matricula_id}", response_model=MatriculaResponse)
async def actualizar_matricula(
    matricula_id: int,
    datos: MatriculaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_no_auxiliar),
    matricula_service: MatriculaService = Depends(get_matricula_service),
):
    """Modificar modalidad u otros campos (no periodo ni alumno)."""
    try:
        return matricula_service.actualizar(db, matricula_id, datos)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{matricula_id}/retirar", response_model=MatriculaResponse)
async def retirar_alumno(
    matricula_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_no_auxiliar),
    matricula_service: MatriculaService = Depends(get_matricula_service),
):
    """Marca la matrícula como 'retirado'. Bloqueado para AUXILIAR."""
    try:
        return matricula_service.retirar(db, matricula_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{matricula_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_matricula(
    matricula_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_no_auxiliar),
    matricula_service: MatriculaService = Depends(get_matricula_service)
):
    """Eliminar matrícula permanentemente. Bloqueado para AUXILIAR."""
    try:
        matricula_service.eliminar(db, matricula_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
