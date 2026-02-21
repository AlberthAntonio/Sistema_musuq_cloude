"""
Rutas CRUD para alumnos - Usando capa de servicios.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.alumno import AlumnoCreate, AlumnoResponse, AlumnoUpdate, AlumnoResumen
from app.services.alumno_service import alumno_service
from app.api.routes.auth import get_current_user, require_role

router = APIRouter()


@router.get("/", response_model=List[AlumnoResponse])
async def listar_alumnos(
    skip: int = 0,
    limit: int = 100,
    grupo: Optional[str] = Query(None, description="Filtrar por grupo (A, B, C, D)"),
    carrera: Optional[str] = Query(None, description="Filtrar por carrera"),
    modalidad: Optional[str] = Query(None, description="Filtrar por modalidad"),
    horario: Optional[str] = Query(None, description="Filtrar por horario (MATUTINO, VESPERTINO)"),
    activo: Optional[bool] = Query(True, description="Filtrar por estado activo"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todos los alumnos con filtros opcionales."""
    return alumno_service.listar(db, skip, limit, grupo, carrera, modalidad, horario, activo)


@router.post("/", response_model=AlumnoResponse, status_code=status.HTTP_201_CREATED)
async def crear_alumno(
    alumno: AlumnoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin", "secretaria"))
):
    """Crear nuevo alumno."""
    try:
        return alumno_service.crear(db, alumno)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/buscar", response_model=List[AlumnoResumen])
async def buscar_alumnos(
    q: str = Query(..., min_length=2, description="Término de búsqueda"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Buscar alumnos por nombre, apellido, DNI o código de matrícula."""
    alumnos = alumno_service.buscar(db, q)
    return [
        {
            "id": a.id,
            "codigo_matricula": a.codigo_matricula,
            "dni": a.dni,
            "nombre_completo": a.nombre_completo,
            "grupo": a.grupo,
            "activo": a.activo
        }
        for a in alumnos
    ]


@router.get("/por-grupo/{grupo}", response_model=List[AlumnoResumen])
async def listar_por_grupo(
    grupo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar alumnos de un grupo específico."""
    alumnos = alumno_service.listar_por_grupo(db, grupo)
    return [
        {
            "id": a.id,
            "codigo_matricula": a.codigo_matricula,
            "dni": a.dni,
            "nombre_completo": a.nombre_completo,
            "grupo": a.grupo,
            "activo": a.activo
        }
        for a in alumnos
    ]


@router.get("/{alumno_id}", response_model=AlumnoResponse)
async def obtener_alumno(
    alumno_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener alumno por ID."""
    alumno = alumno_service.obtener_por_id(db, alumno_id)
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    return alumno


@router.get("/codigo/{codigo}", response_model=AlumnoResponse)
async def obtener_por_codigo(
    codigo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener alumno por código de matrícula."""
    alumno = alumno_service.obtener_por_codigo(db, codigo)
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    return alumno


@router.get("/dni/{dni}", response_model=AlumnoResponse)
async def obtener_por_dni(
    dni: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener alumno por DNI."""
    alumno = alumno_service.obtener_por_dni(db, dni)
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    return alumno


@router.put("/{alumno_id}", response_model=AlumnoResponse)
async def actualizar_alumno(
    alumno_id: int,
    alumno_update: AlumnoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin", "secretaria"))
):
    """Actualizar alumno."""
    try:
        return alumno_service.actualizar(db, alumno_id, alumno_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{alumno_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_alumno(
    alumno_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin"))
):
    """Eliminar alumno (solo admin)."""
    try:
        alumno_service.eliminar(db, alumno_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{alumno_id}/desactivar", response_model=AlumnoResponse)
async def desactivar_alumno(
    alumno_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin", "secretaria"))
):
    """Desactivar alumno (soft delete)."""
    try:
        return alumno_service.desactivar(db, alumno_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
