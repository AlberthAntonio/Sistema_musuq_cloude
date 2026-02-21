"""
Rutas CRUD para listas guardadas.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.lista import ListaCreate, ListaUpdate, ListaResponse, ListaAddAlumnos
from app.services.lista_service import lista_service
from app.api.routes.auth import get_current_user

router = APIRouter()


@router.get("/")
async def listar_listas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todas las listas."""
    return lista_service.listar(db)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def crear_lista(
    lista: ListaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear nueva lista."""
    return lista_service.crear(db, lista)


@router.get("/{lista_id}")
async def obtener_lista(
    lista_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener lista con sus alumnos."""
    lista = lista_service.obtener_con_alumnos(db, lista_id)
    if not lista:
        raise HTTPException(status_code=404, detail="Lista no encontrada")
    return lista


@router.put("/{lista_id}")
async def actualizar_lista(
    lista_id: int,
    lista_update: ListaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar lista."""
    try:
        return lista_service.actualizar(db, lista_id, lista_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{lista_id}/alumnos")
async def agregar_alumnos(
    lista_id: int,
    datos: ListaAddAlumnos,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Agregar alumnos a una lista."""
    try:
        return lista_service.agregar_alumnos(db, lista_id, datos.alumno_ids)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{lista_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_lista(
    lista_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar lista."""
    try:
        lista_service.eliminar(db, lista_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
