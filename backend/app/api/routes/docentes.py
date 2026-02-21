"""
Rutas CRUD para docentes - Usando capa de servicios.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.docente import DocenteCreate, DocenteUpdate, DocenteResponse, DocenteResumen
from app.services.docente_service import docente_service
from app.api.routes.auth import get_current_user, require_role

router = APIRouter()


@router.get("/", response_model=List[DocenteResponse])
async def listar_docentes(
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo (omitir = todos)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar docentes."""
    return docente_service.listar(db, activo)


@router.post("/", response_model=DocenteResponse, status_code=status.HTTP_201_CREATED)
async def crear_docente(
    docente: DocenteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Crear nuevo docente (solo admin)."""
    try:
        return docente_service.crear(db, docente)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/buscar", response_model=List[DocenteResumen])
async def buscar_docentes(
    q: str = Query(..., min_length=2, description="Término de búsqueda"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Buscar docentes por nombre, apellido o DNI."""
    docentes = docente_service.buscar(db, q)
    return [
        {
            "id": d.id,
            "nombre_completo": d.nombre_completo,
            "especialidad": d.especialidad,
            "activo": d.activo
        }
        for d in docentes
    ]


@router.get("/{docente_id}", response_model=DocenteResponse)
async def obtener_docente(
    docente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener docente por ID."""
    docente = docente_service.obtener_por_id(db, docente_id)
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    return docente


@router.put("/{docente_id}", response_model=DocenteResponse)
async def actualizar_docente(
    docente_id: int,
    docente_update: DocenteUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Actualizar docente (solo admin)."""
    try:
        return docente_service.actualizar(db, docente_id, docente_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{docente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_docente(
    docente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Eliminar docente (solo admin)."""
    try:
        docente_service.eliminar(db, docente_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{docente_id}/desactivar", response_model=DocenteResponse)
async def desactivar_docente(
    docente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Desactivar docente (soft delete)."""
    try:
        return docente_service.desactivar(db, docente_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
