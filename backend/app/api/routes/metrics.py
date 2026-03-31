"""
Rutas de métricas del sistema.
Expone resumen de rendimiento para monitoreo operativo.
"""
from fastapi import APIRouter, Depends

from app.core.metrics import metrics_collector
from app.db.database import engine
from app.models.usuario import Usuario
from app.api.routes.auth import get_current_user, require_role

router = APIRouter()


from app.core.cache import cached

@router.get("/summary")
@cached(ttl=5)
async def metrics_summary(
    current_user: Usuario = Depends(require_role("admin")),
):
    """
    Resumen de métricas: latencias p50/p95/p99 por endpoint,
    query counts, error rate, uptime. Cacheado por 5s para evitar DDOS de monitoreo.
    Solo accesible para admin.
    """
    return metrics_collector.get_summary()


@router.get("/health-detailed")
async def health_detailed(
    current_user: Usuario = Depends(require_role("admin")),
):
    """
    Health check detallado con info de pool de conexiones.
    """
    pool_status = {}
    try:
        pool = engine.pool
        pool_status = {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.status(),
        }
    except Exception as e:
        pool_status = {"error": str(e), "note": "SQLite no expone pool stats"}

    summary = metrics_collector.get_summary()
    return {
        "status": "healthy",
        "uptime_seconds": summary["uptime_seconds"],
        "total_requests": summary["total_requests"],
        "error_rate_pct": summary["error_rate_pct"],
        "db_pool": pool_status,
    }


@router.post("/reset")
async def reset_metrics(
    current_user: Usuario = Depends(require_role("admin")),
):
    """Reset de métricas (para antes de un benchmark)."""
    metrics_collector.reset()
    return {"message": "Métricas reseteadas"}
