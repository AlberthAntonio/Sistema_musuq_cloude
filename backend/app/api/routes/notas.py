"""
Rutas CRUD para notas.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.nota import NotaCreate, NotaUpdate, NotaResponse, NotasMasivas
from app.services.nota_service import nota_service
from app.api.routes.auth import get_current_user

router = APIRouter()


@router.get("/por-sesion/{sesion_id}")
async def notas_por_sesion(
    sesion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener notas de una sesión."""
    return nota_service.listar_por_sesion(db, sesion_id)


@router.get("/por-alumno/{alumno_id}")
async def notas_por_alumno(
    alumno_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener notas de un alumno."""
    return nota_service.listar_por_alumno(db, alumno_id)


@router.post("/", response_model=NotaResponse, status_code=status.HTTP_201_CREATED)
async def crear_nota(
    nota: NotaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear nueva nota."""
    try:
        return nota_service.crear(db, nota)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/masivo")
async def crear_notas_masivo(
    datos: NotasMasivas,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear notas masivamente para una sesión."""
    notas = nota_service.crear_masivo(db, datos.sesion_id, datos.notas)
    return {"message": f"Se crearon {len(notas)} notas", "cantidad": len(notas)}


@router.get("/{nota_id}", response_model=NotaResponse)
async def obtener_nota(
    nota_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener nota por ID."""
    nota = nota_service.obtener_por_id(db, nota_id)
    if not nota:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return nota


@router.put("/{nota_id}", response_model=NotaResponse)
async def actualizar_nota(
    nota_id: int,
    nota_update: NotaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar nota."""
    try:
        return nota_service.actualizar(db, nota_id, nota_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{nota_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_nota(
    nota_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar nota."""
    try:
        nota_service.eliminar(db, nota_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
