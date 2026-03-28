"""
Rutas CRUD para matrículas.
Con RBAC: AUXILIAR no puede crear/actualizar/eliminar matrículas.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.matricula import (
    MatriculaCreate, MatriculaUpdate, MatriculaResponse, MatriculaConAlumno
)
from app.services.matricula_service import matricula_service
from app.api.routes.auth import get_current_user, verificar_no_auxiliar

router = APIRouter()


@router.get("/", response_model=List[MatriculaResponse])
async def listar_matriculas(
    periodo_id: Optional[int] = Query(None, description="Filtrar por periodo académico"),
    alumno_id: Optional[int] = Query(None, description="Filtrar por alumno"),
    grupo: Optional[str] = Query(None, description="Filtrar por grupo"),
    estado: Optional[str] = Query("activo", description="Filtrar por estado"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar matrículas con filtros opcionales."""
    return matricula_service.listar(db, periodo_id, alumno_id, grupo, estado, skip, limit)


@router.post("/", response_model=MatriculaResponse, status_code=status.HTTP_201_CREATED)
async def crear_matricula(
    matricula: MatriculaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_no_auxiliar)
):
    """Crear nueva matrícula. Bloqueado para AUXILIAR."""
    try:
        return matricula_service.crear(db, matricula, usuario_actual_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{matricula_id}", response_model=MatriculaResponse)
async def obtener_matricula(
    matricula_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener matrícula por ID."""
    matricula = matricula_service.obtener_por_id(db, matricula_id)
    if not matricula:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")
    return matricula


@router.get("/codigo/{codigo}", response_model=MatriculaResponse)
async def obtener_por_codigo(
    codigo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener matrícula por código."""
    matricula = matricula_service.obtener_por_codigo(db, codigo)
    if not matricula:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")
    return matricula


@router.put("/{matricula_id}", response_model=MatriculaResponse)
async def actualizar_matricula(
    matricula_id: int,
    matricula_update: MatriculaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_no_auxiliar)
):
    """Actualizar matrícula. Bloqueado para AUXILIAR."""
    try:
        return matricula_service.actualizar(db, matricula_id, matricula_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{matricula_id}/retirar", response_model=MatriculaResponse)
async def retirar_matricula(
    matricula_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_no_auxiliar)
):
    """Marcar matrícula como retirada. Bloqueado para AUXILIAR."""
    try:
        return matricula_service.retirar(db, matricula_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{matricula_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_matricula(
    matricula_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_no_auxiliar)
):
    """Eliminar matrícula permanentemente. Bloqueado para AUXILIAR."""
    try:
        matricula_service.eliminar(db, matricula_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
