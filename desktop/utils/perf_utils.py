"""
Utilidades de rendimiento y logging para Desktop
Sistema Musuq Cloud

Proporciona:
- ViewProfiler: medición de tiempos por vista (import, create, paint, data)
- logger centralizado con niveles configurables
"""

import time
import logging
import statistics
from typing import Dict, List, Optional
from contextlib import contextmanager


# ============================================================
# LOGGER CENTRALIZADO
# ============================================================

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Obtener logger configurado para el módulo.
    Uso:
        from utils.perf_utils import get_logger
        logger = get_logger(__name__)
        logger.info("mensaje")
        logger.debug("detalle")  # solo visible si level=DEBUG
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(levelname)s] %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


# Logger global del módulo
logger = get_logger("musuq.perf")


# ============================================================
# VIEW PROFILER
# ============================================================

class ViewProfiler:
    """
    Perfilador de rendimiento para vistas.
    
    Mide tiempos de:
    - show_view: latencia total al cambiar de vista
    - import: tiempo de importar módulo de vista
    - create: tiempo de crear widgets
    - paint: tiempo hasta primer renderizado
    - data: tiempo de carga de datos
    
    Almacena historial por módulo para calcular p50/p95.
    """
    
    def __init__(self):
        self._metrics: Dict[str, List[float]] = {}
        self._active_timers: Dict[str, float] = {}
        self._seen_views: set = set()  # Para distinguir primera carga vs cacheada
    
    def start(self, view_key: str, phase: str = "show_view"):
        """Iniciar medición de una fase"""
        key = f"{view_key}.{phase}"
        self._active_timers[key] = time.perf_counter()
    
    def stop(self, view_key: str, phase: str = "show_view") -> float:
        """Finalizar medición y registrar resultado. Retorna ms."""
        key = f"{view_key}.{phase}"
        start = self._active_timers.pop(key, None)
        if start is None:
            return 0.0
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        if key not in self._metrics:
            self._metrics[key] = []
        self._metrics[key].append(elapsed_ms)
        
        # Log según tipo de carga
        if phase == "show_view":
            is_first = view_key not in self._seen_views
            self._seen_views.add(view_key)
            
            if is_first:
                if elapsed_ms > 2000:
                    logger.warning(
                        f"⚠ Vista '{view_key}' primera carga: {elapsed_ms:.0f}ms "
                        f"(lenta, considerar optimizar __init__)"
                    )
                else:
                    logger.info(
                        f"📊 Vista '{view_key}' primera carga: {elapsed_ms:.0f}ms"
                    )
            else:
                # Carga cacheada - aquí sí aplicamos el objetivo de 120ms
                if elapsed_ms > 120:
                    logger.warning(
                        f"⚠ Vista '{view_key}' cacheada: {elapsed_ms:.0f}ms "
                        f"(objetivo: ≤120ms)"
                    )
                else:
                    logger.debug(f"✓ Vista '{view_key}' cacheada: {elapsed_ms:.0f}ms")
        
        return elapsed_ms
    
    @contextmanager
    def measure(self, view_key: str, phase: str = "show_view"):
        """Context manager para medir una fase"""
        self.start(view_key, phase)
        try:
            yield
        finally:
            self.stop(view_key, phase)
    
    def get_stats(self, view_key: str, phase: str = "show_view") -> Dict:
        """Obtener estadísticas de una vista/fase"""
        key = f"{view_key}.{phase}"
        values = self._metrics.get(key, [])
        
        if not values:
            return {"count": 0, "p50": 0, "p95": 0, "min": 0, "max": 0}
        
        sorted_vals = sorted(values)
        return {
            "count": len(values),
            "p50": statistics.median(sorted_vals),
            "p95": sorted_vals[int(len(sorted_vals) * 0.95)] if len(sorted_vals) >= 2 else sorted_vals[-1],
            "min": min(sorted_vals),
            "max": max(sorted_vals),
        }
    
    def report(self) -> str:
        """Generar reporte de rendimiento de todas las vistas"""
        lines = ["=" * 60, "REPORTE DE RENDIMIENTO - Musuq Desktop", "=" * 60]
        
        # Agrupar por vista
        views = set()
        for key in self._metrics:
            view_key = key.rsplit(".", 1)[0]
            views.add(view_key)
        
        for view in sorted(views):
            lines.append(f"\n📊 {view}:")
            for key, values in sorted(self._metrics.items()):
                if key.startswith(f"{view}."):
                    phase = key.rsplit(".", 1)[1]
                    stats = self.get_stats(view, phase)
                    lines.append(
                        f"  {phase:15s} | "
                        f"p50: {stats['p50']:6.0f}ms | "
                        f"p95: {stats['p95']:6.0f}ms | "
                        f"n={stats['count']}"
                    )
        
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


# Instancia global del profiler
profiler = ViewProfiler()
