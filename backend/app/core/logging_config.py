"""
Configuración de logging estructurado para producción.
Soporta formato JSON (producción) y Pretty (desarrollo).
"""
import logging
import json
import sys
import contextvars
from datetime import datetime
from typing import Any, Dict

from app.core.config import settings

# Global ContextVar para guardar el Request ID de las trazas
request_id_var = contextvars.ContextVar("request_id", default=None)

_RESERVED_LOG_RECORD_KEYS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
    "asctime",
}


def _to_json_safe(value: Any) -> Any:
    """Convierte valores no serializables en texto para logging JSON."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple, set)):
        return [_to_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _to_json_safe(v) for k, v in value.items()}
    return str(value)

class JsonFormatter(logging.Formatter):
    """Formateador JSON para logging estructurado en producción."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        req_id = request_id_var.get()
        if req_id:
            log_entry["request_id"] = req_id
        elif hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "method"):
            log_entry["method"] = record.method
        if hasattr(record, "path"):
            log_entry["path"] = record.path
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms

        extra_context: Dict[str, Any] = {}
        for key, value in record.__dict__.items():
            if key in _RESERVED_LOG_RECORD_KEYS:
                continue
            if key in {"request_id", "method", "path", "status_code", "duration_ms"}:
                continue
            extra_context[key] = _to_json_safe(value)

        if extra_context:
            log_entry["context"] = extra_context

        return json.dumps(log_entry, ensure_ascii=False)


def _apply_handler(logger_name: str, handler: logging.Handler, level: int) -> None:
    """Aplica el handler a un logger específico desactivando la propagación al root."""
    log = logging.getLogger(logger_name)
    log.handlers.clear()
    log.addHandler(handler)
    log.setLevel(level)
    log.propagate = False  # evita que suba al root logger (donde viven handlers duplicados)


def setup_logging() -> None:
    """Configura el sistema de logging según el entorno."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    use_json = settings.LOG_FORMAT.lower() == "json" and not settings.DEBUG

    # Configurar handler de salida estándar
    handler = logging.StreamHandler(sys.stdout)

    if use_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))

    # --- Root logger: un solo handler limpio ---
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)

    # --- Loggers con propagación cortada para evitar duplicados ---
    # SQLAlchemy: el más propenso a aparecer doble por la propagación al root
    # sa_engine_level = logging.INFO if settings.DEBUG else logging.WARNING
    sa_engine_level = logging.WARNING
    _apply_handler("sqlalchemy.engine", handler, sa_engine_level)
    _apply_handler("sqlalchemy",        handler, sa_engine_level)

    # Uvicorn: ya tiene sus propios handlers; solo ajustamos nivel
    _apply_handler("uvicorn",        handler, logging.INFO)
    _apply_handler("uvicorn.error",  handler, logging.INFO)
    _apply_handler("uvicorn.access", handler, logging.WARNING)

    # App principal
    _apply_handler("musuq", handler, log_level)

    # Otros ruidosos
    logging.getLogger("passlib").setLevel(logging.WARNING)


# Logger principal de la aplicación
logger = logging.getLogger("musuq")
