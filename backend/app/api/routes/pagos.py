"""
Rutas CRUD para pagos - Vinculados a obligaciones.
Con RBAC: AUXILIAR no puede crear/actualizar/eliminar pagos.
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.pago import PagoCreate, PagoUpdate, PagoResponse, PagoConDetalle
from app.api.routes.auth import get_current_user, verificar_no_auxiliar
from app.dependencies import get_pago_service
from app.services.pago_service import PagoService
from app.core.config import settings
from app.core.pagination import build_paginated_payload

router = APIRouter()


@router.get("/", response_model=List[PagoConDetalle])
async def listar_pagos(
    request: Request,
    response: Response,
    obligacion_id: Optional[int] = Query(None, description="Filtrar por obligación"),
    periodo_id: Optional[int] = Query(None, description="Filtrar por periodo"),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    alumno_id: Optional[int] = Query(None, description="Filtrar por alumno (recorre Matrícula→Obligación→Pago)"),
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
    pago_service: PagoService = Depends(get_pago_service),
):
    """Listar pagos con filtros opcionales."""
    results = pago_service.listar(
        db,
        obligacion_id,
        periodo_id,
        fecha_desde,
        fecha_hasta,
        alumno_id,
        skip,
        limit,
    )
    total_count = pago_service.contar(
        db,
        obligacion_id,
        periodo_id,
        fecha_desde,
        fecha_hasta,
        alumno_id,
    )
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


@router.post("/", response_model=PagoResponse, status_code=status.HTTP_201_CREATED)
async def registrar_pago(
    pago: PagoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_no_auxiliar),
    pago_service: PagoService = Depends(get_pago_service),
):
    """
    Registrar un pago. Actualiza el saldo pagado en la obligación.
    Bloqueado para rol AUXILIAR.
    """
    try:
        return pago_service.crear(db, pago, usuario_actual_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/resumen/matricula/{matricula_id}")
async def resumen_pagos_matricula(
    matricula_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    pago_service: PagoService = Depends(get_pago_service),
):
    """Obtener resumen financiero de una matrícula (monto total vs pagado global)."""
    try:
        return pago_service.resumen_por_matricula(db, matricula_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{pago_id}", response_model=PagoResponse)
async def obtener_pago(
    pago_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    pago_service: PagoService = Depends(get_pago_service),
):
    """Obtener pago por ID."""
    pago = pago_service.obtener_por_id(db, pago_id)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago


@router.put("/{pago_id}", response_model=PagoResponse)
async def actualizar_pago(
    pago_id: int,
    pago_update: PagoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_no_auxiliar),
    pago_service: PagoService = Depends(get_pago_service),
):
    """Actualizar datos generales del pago (admin, secretaria)."""
    try:
        return pago_service.actualizar(db, pago_id, pago_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{pago_id}", status_code=status.HTTP_204_NO_CONTENT)
async def anular_pago(
    pago_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_no_auxiliar),
    pago_service: PagoService = Depends(get_pago_service),
):
    """Anular pago, revirtiendo el monto en la obligación. Bloqueado para AUXILIAR."""
    try:
        pago_service.eliminar(db, pago_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
