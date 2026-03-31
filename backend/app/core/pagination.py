"""
Utilidades de paginación estandarizada.
Mantiene compatibilidad con el formato List[...] actual del desktop,
al mismo tiempo que agrega header X-Total-Count.
"""
from typing import Any, Dict, List, Optional, Tuple
from fastapi import Query, Request, Response
from sqlalchemy.orm import Query as SAQuery

from app.core.config import settings


class PaginationParams:
    """Dependency de paginación reutilizable en endpoints."""

    def __init__(
        self,
        skip: int = Query(0, ge=0, alias="skip", description="Offset de paginación"),
        limit: int = Query(
            settings.DEFAULT_PAGE_SIZE,
            ge=1,
            le=settings.MAX_PAGE_SIZE,
            alias="limit",
            description="Registros por página (max 200)",
        ),
    ):
        self.skip = skip
        self.limit = limit


def paginate_query(
    query: SAQuery,
    skip: int,
    limit: int,
    include_total: bool = True,
) -> Tuple[List[Any], Optional[int], bool]:
    """
    Aplica paginación a un query SQLAlchemy.

    Retorna: (items, total, has_next)
    """
    total = query.order_by(None).count() if include_total else None
    items = query.offset(skip).limit(limit).all()
    if total is not None:
        has_next = (skip + limit) < total
    else:
        has_next = len(items) == limit
    return items, total, has_next


def build_paginated_payload(
    data: List[Any],
    limit: int,
    offset: int,
    total: int,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Construye la respuesta estandarizada {data, meta}."""
    return {
        "data": data,
        "meta": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_next": (offset + limit) < total,
            "request_id": request_id,
        },
    }
