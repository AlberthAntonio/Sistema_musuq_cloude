"""
Sistema Musuq Cloud - Backend API
================================
API REST con FastAPI para el sistema de asistencia multiusuario.
Arquitectura multi-tenant por Periodos Académicos.
Versión 2.1.0 - Production Ready
"""
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging_config import setup_logging, logger
from app.api.routes import (
    auth, usuarios, alumnos, asistencia, health,
    cursos, docentes, horarios, eventos, listas, notas, pagos, sesiones, aulas,
    periodos, matriculas, obligaciones, reportes
)

# ---------------------------------------------------------------------------
# Inicializar logging ANTES de crear la app
# ---------------------------------------------------------------------------
setup_logging()


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eventos de inicio y parada de la aplicación."""
   
    setup_logging()
    logger.info(
        "Iniciando %s v2.1.0 | DEBUG=%s | DB=%s",
        settings.APP_NAME,
        settings.DEBUG,
        "SQLite" if settings.USE_SQLITE else "PostgreSQL"
    )
    yield
    logger.info("Apagando %s", settings.APP_NAME)


# ---------------------------------------------------------------------------
# Crear aplicación FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "API REST para Sistema de Asistencia Multiusuario.\n"
        "Arquitectura multi-tenant por Periodos Académicos.\n\n"
        "**Autenticación**: Bearer token JWT. Usar `/auth/login` para obtener tokens."
    ),
    version="2.1.0",
    docs_url="/docs" if settings.DEBUG else None,   # Ocultar Swagger en producción
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware: CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Total-Count", "X-Request-ID"],
)

# ---------------------------------------------------------------------------
# Middleware: Request ID + logging de peticiones
# ---------------------------------------------------------------------------
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Asigna un ID único a cada petición y registra duración + status."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    start_time = time.time()

    # Inyectar request_id en el state para que los handlers puedan usarlo
    request.state.request_id = request_id

    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 1)
        logger.error(
            "Unhandled error | %s %s | %sms | req_id=%s",
            request.method, request.url.path, duration_ms, request_id,
            exc_info=exc
        )
        raise

    duration_ms = round((time.time() - start_time) * 1000, 1)
    level = logging.WARNING if response.status_code >= 400 else logging.INFO
    logger.log(
        level,
        "%s %s -> %s | %sms | req_id=%s",
        request.method, request.url.path, response.status_code, duration_ms, request_id
    )
    response.headers["X-Request-ID"] = request_id
    return response


# ---------------------------------------------------------------------------
# Manejadores globales de errores
# ---------------------------------------------------------------------------
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handler unificado para errores HTTP."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
        },
        headers=getattr(exc, "headers", None) or {},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler para errores de validación Pydantic - devuelve detalles claros."""
    errores = []
    for error in exc.errors():
        errores.append({
            "campo": " -> ".join(str(loc) for loc in error["loc"]),
            "mensaje": error["msg"],
            "tipo": error["type"],
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Error de validación en los datos enviados",
            "errores": errores,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Captura excepciones no manejadas para evitar exponer stack traces."""
    logger.exception(
        "Excepción no manejada | %s %s | req_id=%s",
        request.method, request.url.path,
        getattr(request.state, "request_id", "?")
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor. Contacta al administrador."},
    )


# ---------------------------------------------------------------------------
# Registrar rutas
# ---------------------------------------------------------------------------
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
app.include_router(usuarios.router, prefix="/usuarios", tags=["Usuarios"])
app.include_router(periodos.router, prefix="/periodos", tags=["Periodos Académicos"])
app.include_router(alumnos.router, prefix="/alumnos", tags=["Alumnos"])
app.include_router(matriculas.router, prefix="/matriculas", tags=["Matrículas"])
app.include_router(obligaciones.router, prefix="/obligaciones", tags=["Obligaciones de Pago"])
app.include_router(pagos.router, prefix="/pagos", tags=["Pagos"])
app.include_router(asistencia.router, prefix="/asistencia", tags=["Asistencia"])
app.include_router(cursos.router, prefix="/cursos", tags=["Cursos"])
app.include_router(aulas.router, prefix="/aulas", tags=["Aulas"])
app.include_router(docentes.router, prefix="/docentes", tags=["Docentes"])
app.include_router(horarios.router, prefix="/horarios", tags=["Horarios"])
app.include_router(eventos.router, prefix="/eventos", tags=["Eventos"])
app.include_router(listas.router, prefix="/listas", tags=["Listas"])
app.include_router(notas.router, prefix="/notas", tags=["Notas"])
app.include_router(sesiones.router, prefix="/sesiones", tags=["Sesiones"])
app.include_router(reportes.router, prefix="/reportes", tags=["Reportes"])


# ---------------------------------------------------------------------------
# Endpoint raíz (siempre disponible incluso sin docs)
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def root():
    """Endpoint raíz - verificación rápida."""
    return {
        "app": settings.APP_NAME,
        "version": "2.1.0",
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled in production",
    }
