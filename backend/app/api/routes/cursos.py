"""
Rutas CRUD para cursos - Usando capa de servicios.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.curso import (
    CursoCreate, CursoUpdate, CursoResponse,
    MallaCurricularCreate, MallaCurricularResponse
)
from app.services.curso_service import curso_service
from app.api.routes.auth import get_current_user, require_role

router = APIRouter()


# ==================== CURSOS ====================

@router.get("/", response_model=List[CursoResponse])
async def listar_cursos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todos los cursos."""
    return curso_service.listar_cursos(db)


@router.post("/", response_model=CursoResponse, status_code=status.HTTP_201_CREATED)
async def crear_curso(
    curso: CursoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Crear nuevo curso (solo admin)."""
    try:
        return curso_service.crear_curso(db, curso)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{curso_id}", response_model=CursoResponse)
async def obtener_curso(
    curso_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener curso por ID."""
    curso = curso_service.obtener_curso(db, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    return curso


@router.put("/{curso_id}", response_model=CursoResponse)
async def actualizar_curso(
    curso_id: int,
    curso_update: CursoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Actualizar curso (solo admin)."""
    try:
        return curso_service.actualizar_curso(db, curso_id, curso_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{curso_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_curso(
    curso_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Eliminar curso (solo admin)."""
    try:
        curso_service.eliminar_curso(db, curso_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== MALLA CURRICULAR ====================

@router.get("/malla/", response_model=List[MallaCurricularResponse])
async def listar_malla(
    grupo: Optional[str] = Query(None, description="Filtrar por grupo"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar asignaciones de malla curricular."""
    return curso_service.listar_malla(db, grupo)


@router.post("/malla/", response_model=MallaCurricularResponse, status_code=status.HTTP_201_CREATED)
async def asignar_curso_a_grupo(
    malla: MallaCurricularCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Asignar curso a un grupo (solo admin)."""
    try:
        return curso_service.asignar_curso_a_grupo(db, malla)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/malla/{malla_id}", status_code=status.HTTP_204_NO_CONTENT)
async def quitar_curso_de_grupo(
    malla_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Quitar asignación de curso de grupo (solo admin)."""
    try:
        curso_service.quitar_curso_de_grupo(db, malla_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/por-grupo/{grupo}", response_model=List[CursoResponse])
async def cursos_por_grupo(
    grupo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener cursos asignados a un grupo."""
    return curso_service.cursos_por_grupo(db, grupo)
