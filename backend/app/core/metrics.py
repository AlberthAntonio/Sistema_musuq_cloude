"""
Módulo de métricas e instrumentación del backend.
Registra latencia por endpoint, conteo de queries, y expone un resumen.
"""
import time
import threading
from collections import defaultdict
from datetime import datetime
from contextvars import ContextVar
from typing import Any, Dict, List

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import logger


class MetricsCollector:
    """Recolector de métricas in-memory con thread safety."""

    def __init__(self):
        self._lock = threading.Lock()
        self._latencies: Dict[str, List[float]] = defaultdict(list)
        self._status_counts: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self._query_counts: Dict[str, List[int]] = defaultdict(list)
        self._request_count: int = 0
        self._error_count: int = 0
        self._start_time: datetime = datetime.utcnow()
        # Máximo de muestras por endpoint para evitar memory leak
        self.MAX_SAMPLES = 2000

    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        query_count: int = 0,
    ):
        """Registra métricas de un request completado."""
        key = f"{method} {path}"
        with self._lock:
            self._request_count += 1
            if status_code >= 500:
                self._error_count += 1

            # Latencia
            samples = self._latencies[key]
            samples.append(duration_ms)
            if len(samples) > self.MAX_SAMPLES:
                self._latencies[key] = samples[-self.MAX_SAMPLES:]

            # Status codes
            self._status_counts[key][status_code] += 1

            # Query count
            qc_samples = self._query_counts[key]
            qc_samples.append(query_count)
            if len(qc_samples) > self.MAX_SAMPLES:
                self._query_counts[key] = qc_samples[-self.MAX_SAMPLES:]

    def _percentile(self, data: List[float], p: float) -> float:
        if not data:
            return 0.0
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * (p / 100.0)
        f = int(k)
        c = f + 1
        if c >= len(sorted_data):
            return round(sorted_data[f], 2)
        return round(sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f]), 2)

    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumen de métricas."""
        with self._lock:
            uptime_seconds = (datetime.utcnow() - self._start_time).total_seconds()
            endpoints = {}
            for key, samples in self._latencies.items():
                if not samples:
                    continue
                qc = self._query_counts.get(key, [])
                endpoints[key] = {
                    "request_count": sum(self._status_counts[key].values()),
                    "latency_p50_ms": self._percentile(samples, 50),
                    "latency_p95_ms": self._percentile(samples, 95),
                    "latency_p99_ms": self._percentile(samples, 99),
                    "latency_avg_ms": round(sum(samples) / len(samples), 2),
                    "latency_max_ms": round(max(samples), 2),
                    "avg_query_count": round(sum(qc) / len(qc), 1) if qc else 0,
                    "status_codes": dict(self._status_counts[key]),
                }
            return {
                "uptime_seconds": round(uptime_seconds, 1),
                "total_requests": self._request_count,
                "total_errors_5xx": self._error_count,
                "error_rate_pct": round(
                    (self._error_count / self._request_count * 100) if self._request_count > 0 else 0, 3
                ),
                "endpoints": endpoints,
                "collected_at": datetime.utcnow().isoformat() + "Z",
            }

    def reset(self):
        """Reset de métricas (para tests)."""
        with self._lock:
            self._latencies.clear()
            self._status_counts.clear()
            self._query_counts.clear()
            self._request_count = 0
            self._error_count = 0
            self._start_time = datetime.utcnow()


# Instancia global del recolector
metrics_collector = MetricsCollector()

# ContextVar para rastrear el conteo de queries de forma aislada por petición
_query_count_context: ContextVar[int] = ContextVar("query_count", default=0)
_sql_listener_registered = False
_sql_listener_lock = threading.Lock()

def _sql_query_listener(*args, **kwargs):
    """Incrementa el contador de queries en el contexto actual."""
    current = _query_count_context.get()
    _query_count_context.set(current + 1)

def register_sql_metrics(engine):
    """Registra el listener global de SQL una sola vez."""
    global _sql_listener_registered
    if _sql_listener_registered:
        return

    with _sql_listener_lock:
        if _sql_listener_registered:
            return
        from sqlalchemy import event
        event.listen(engine, "before_cursor_execute", _sql_query_listener)
        _sql_listener_registered = True





class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware que registra métricas de latencia y queries por request."""

    # Rutas que no queremos instrumentar
    SKIP_PATHS = {"/docs", "/redoc", "/openapi.json", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip rutas internas
        if path in self.SKIP_PATHS or path.startswith("/metrics"):
            return await call_next(request)

        # Normalizar path (reemplazar IDs numéricos por {id})
        normalized = self._normalize_path(path)

        # Iniciar conteo de queries para este contexto
        token = _query_count_context.set(0)

        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            final_query_count = _query_count_context.get()
            _query_count_context.reset(token)

        metrics_collector.record_request(
            method=request.method,
            path=normalized,
            status_code=response.status_code,
            duration_ms=duration_ms,
            query_count=final_query_count,
        )

        # Agregar header de performance
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        return response

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Reemplaza segmentos numéricos por {id} para agrupar métricas."""
        parts = path.strip("/").split("/")
        normalized = []
        for part in parts:
            if part.isdigit():
                normalized.append("{id}")
            else:
                normalized.append(part)
        return "/" + "/".join(normalized)
