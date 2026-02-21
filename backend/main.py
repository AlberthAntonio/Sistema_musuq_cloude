"""
Sistema Musuq Cloud - Backend API
================================
API REST con FastAPI para el sistema de asistencia multiusuario.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import (
    auth, usuarios, alumnos, asistencia, health, 
    cursos, docentes, horarios, eventos, listas, notas, pagos, sesiones
)

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="API REST para Sistema de Asistencia Multiusuario",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS para permitir conexiones del cliente desktop
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, limitar a IPs específicas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
app.include_router(usuarios.router, prefix="/usuarios", tags=["Usuarios"])
app.include_router(alumnos.router, prefix="/alumnos", tags=["Alumnos"])
app.include_router(asistencia.router, prefix="/asistencia", tags=["Asistencia"])
app.include_router(cursos.router, prefix="/cursos", tags=["Cursos"])
app.include_router(docentes.router, prefix="/docentes", tags=["Docentes"])
app.include_router(horarios.router, prefix="/horarios", tags=["Horarios"])
app.include_router(eventos.router, prefix="/eventos", tags=["Eventos"])
app.include_router(listas.router, prefix="/listas", tags=["Listas"])
app.include_router(notas.router, prefix="/notas", tags=["Notas"])
app.include_router(pagos.router, prefix="/pagos", tags=["Pagos"])
app.include_router(sesiones.router, prefix="/sesiones", tags=["Sesiones"])


@app.get("/")
async def root():
    """Endpoint raíz - verificación rápida"""
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

