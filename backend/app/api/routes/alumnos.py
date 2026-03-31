"""
Rutas CRUD para alumnos - Con filtro multi-tenant por periodo.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Request, UploadFile, File
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.alumno import AlumnoCreate, AlumnoResponse, AlumnoUpdate, AlumnoResumen, AlumnoListItem
from app.api.routes.auth import get_current_user, require_role, verificar_no_auxiliar
from app.dependencies import get_alumno_service
from app.services.alumno_service import AlumnoService
from app.core.config import settings
from app.core.pagination import build_paginated_payload

router = APIRouter()

MAX_FOTO_SIZE_BYTES = 2 * 1024 * 1024
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.get("/", response_model=List[AlumnoListItem])
async def listar_alumnos(
    request: Request,
    response: Response,
    skip: int = Query(0, ge=0, description="Offset de paginación"),
    limit: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Límite de registros por página"
    ),
    activo: Optional[bool] = Query(True, description="Filtrar por estado activo"),
    periodo_id: Optional[int] = Query(None, description="Filtrar por periodo académico"),
    grupo: Optional[str] = Query(None, description="Filtrar por grupo (A, B, C, D…)"),
    modalidad: Optional[str] = Query(None, description="Filtrar por modalidad de matrícula"),
    format: Optional[str] = Query(None, description="Usar 'paginated' para respuesta con data/meta"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    alumno_service: AlumnoService = Depends(get_alumno_service),
):
    """Listar alumnos con filtros opcionales. grupo/modalidad requieren join con matrículas."""
    results = alumno_service.listar(db, skip, limit, activo, periodo_id, grupo, modalidad)
    total_count = alumno_service.contar(db, activo, periodo_id, grupo, modalidad)
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


@router.post("/", response_model=AlumnoResponse, status_code=status.HTTP_201_CREATED)
async def crear_alumno(
    alumno: AlumnoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_no_auxiliar),
    alumno_service: AlumnoService = Depends(get_alumno_service),
):
    """Crea un alumno validando rol, DNI único y retorna la entidad."""
    try:
        return alumno_service.crear(db, alumno, usuario_actual_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{alumno_id}/foto", response_model=AlumnoResponse)
async def subir_foto_alumno(
    alumno_id: int,
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_no_auxiliar),
    alumno_service: AlumnoService = Depends(get_alumno_service),
):
    """Sube o reemplaza la foto del alumno almacenándola como binario en BD."""
    if not archivo.content_type or archivo.content_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de imagen no permitido. Use JPG, PNG o WEBP.",
        )

    contenido = await archivo.read()
    if not contenido:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo vacío")

    if len(contenido) > MAX_FOTO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="La foto no debe superar 2MB",
        )

    try:
        return alumno_service.actualizar_foto(db, alumno_id, contenido, archivo.content_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{alumno_id}/foto")
async def obtener_foto_alumno(
    alumno_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    alumno_service: AlumnoService = Depends(get_alumno_service),
):
    """Retorna la foto del alumno para visualización remota desde otros equipos."""
    try:
        foto_data, mime_type = alumno_service.obtener_foto(db, alumno_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if not foto_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno sin foto registrada")

    return Response(content=foto_data, media_type=(mime_type or "image/jpeg"))


@router.delete("/{alumno_id}/foto", response_model=AlumnoResponse)
async def eliminar_foto_alumno(
    alumno_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_no_auxiliar),
    alumno_service: AlumnoService = Depends(get_alumno_service),
):
    """Elimina la foto asociada al alumno."""
    try:
        return alumno_service.eliminar_foto(db, alumno_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/buscar", response_model=List[AlumnoResumen])
async def buscar_alumnos(
    q: str = Query(..., min_length=2, description="Texto a buscar"),
    limit: int = Query(20, le=50, description="Límite rápido autocomplete"),
    periodo_id: Optional[int] = Query(None, description="Filtrar por periodo matriculado"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    alumno_service: AlumnoService = Depends(get_alumno_service),
):
    """
    Búsqueda rápida por nombre completo o DNI.
    Incluye optimización para autocomplete del frontend.
    """
    return alumno_service.buscar(db, q, limit, periodo_id=periodo_id)


@router.get("/{alumno_id}", response_model=AlumnoResponse)
async def obtener_alumno(
    alumno_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    alumno_service: AlumnoService = Depends(get_alumno_service),
):
    """Obtiene datos personales básicos del alumno."""
    alumno = alumno_service.obtener_por_id(db, alumno_id)
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    return alumno


@router.get("/dni/{dni}", response_model=AlumnoResponse)
async def obtener_alumno_por_dni(
    dni: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    alumno_service: AlumnoService = Depends(get_alumno_service),
):
    """Obtiene un alumno por su DNI. Útil para validaciones."""
    alumno = alumno_service.obtener_por_dni(db, dni)
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    return alumno


@router.put("/{alumno_id}", response_model=AlumnoResponse)
async def actualizar_alumno(
    alumno_id: int,
    datos: AlumnoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_no_auxiliar),
    alumno_service: AlumnoService = Depends(get_alumno_service),
):
    """Edita datos. Valida re-verificación de DNI único y no permite auxiliares."""
    try:
        return alumno_service.actualizar(db, alumno_id, datos)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{alumno_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_alumno(
    alumno_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin", "secretaria")),
    alumno_service: AlumnoService = Depends(get_alumno_service),
):
    """Desactiva o elimina un alumno (Solo admin/secretaria)."""
    try:
        alumno_service.eliminar(db, alumno_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{alumno_id}/desactivar", response_model=AlumnoResponse)
async def desactivar_alumno(
    alumno_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin", "secretaria")),
    alumno_service: AlumnoService = Depends(get_alumno_service)
):
    """Desactivar alumno (soft delete)."""
    try:
        return alumno_service.desactivar(db, alumno_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
