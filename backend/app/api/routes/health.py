"""
Endpoint de health check - verificación de estado del servidor.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db import get_db

router = APIRouter()


@router.get("/health")
async def health_check():
    """Verificación básica de que el servidor está corriendo."""
    return {"status": "healthy", "message": "API funcionando correctamente"}


@router.get("/health/db")
async def health_check_db(db: Session = Depends(get_db)):
    """Verificación de conexión a base de datos."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
