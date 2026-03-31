import time
import functools
import inspect
import threading
import hashlib
import json
from datetime import date, datetime
from typing import Any, Callable, Dict, Optional, Tuple

class TTLCache:
    """
    Caché en memoria súper ligero con Time-To-Live (TTL).
    Diseñado para respuestas repetitivas donde Redis sería overkill.
    """
    def __init__(self, default_ttl: int = 60, max_items: int = 2000):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.Lock()
        self.default_ttl = default_ttl
        self.max_items = max_items

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                expiry, value = self._cache[key]
                if time.time() < expiry:
                    return value
                else:
                    del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        expiry = time.time() + (ttl or self.default_ttl)
        with self._lock:
            # Evita crecimiento sin control: limpia expirados y recorta si es necesario.
            if len(self._cache) >= self.max_items:
                now = time.time()
                expired_keys = [k for k, (exp, _) in self._cache.items() if exp <= now]
                for expired_key in expired_keys:
                    self._cache.pop(expired_key, None)
                if len(self._cache) >= self.max_items and self._cache:
                    oldest_key = next(iter(self._cache))
                    self._cache.pop(oldest_key, None)
            self._cache[key] = (expiry, value)

    def clear(self):
        with self._lock:
            self._cache.clear()

_IGNORE_TYPE_NAMES = {"Session", "Request", "BackgroundTasks", "Usuario"}
_IGNORE_MODULE_PREFIXES = ("sqlalchemy", "starlette", "fastapi")


def _is_infra_object(value: Any) -> bool:
    value_type = type(value)
    if value_type.__name__ in _IGNORE_TYPE_NAMES:
        return True
    module_name = value_type.__module__
    return any(module_name.startswith(prefix) for prefix in _IGNORE_MODULE_PREFIXES)


def _normalize_for_key(value: Any) -> Any:
    """Convierte valores complejos a forma serializable/determinista."""
    if _is_infra_object(value):
        return None

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, dict):
        normalized_dict = {}
        for k in sorted(value.keys(), key=lambda x: str(x)):
            normalized_value = _normalize_for_key(value[k])
            if normalized_value is not None:
                normalized_dict[str(k)] = normalized_value
        return normalized_dict

    if isinstance(value, (list, tuple)):
        return [v for v in (_normalize_for_key(item) for item in value) if v is not None]

    if isinstance(value, set):
        normalized_set = [v for v in (_normalize_for_key(item) for item in value) if v is not None]
        return sorted(normalized_set, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=True))

    value_id = getattr(value, "id", None)
    if isinstance(value_id, (str, int)):
        return {"__type__": type(value).__name__, "id": value_id}

    # Fallback estable: evita repr con direcciones de memoria.
    return {"__type__": type(value).__name__}


def _make_cache_key(func: Callable, args: Tuple, kwargs: Dict) -> str:
    """
    Genera una clave de caché determinista y estable.
    Filtra objetos de infraestructura (Session, Request, etc.) que no deben
    influir en la lógica de negocio del cacheado.
    """
    payload = {
        "module": func.__module__,
        "func": func.__name__,
        "args": [v for v in (_normalize_for_key(arg) for arg in args) if v is not None],
        "kwargs": {
            key: normalized
            for key, normalized in (
                (k, _normalize_for_key(kwargs[k]))
                for k in sorted(kwargs.keys())
            )
            if normalized is not None
        },
    }

    raw_key = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

# Singleton de la aplicación
app_cache = TTLCache(default_ttl=300, max_items=2000)

def cached(ttl: int = 60):
    """
    Decorador para cachear métodos sincrónicos o asincrónicos
    con generación de claves inteligente y estable.
    """
    def decorator(func: Callable):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                key = _make_cache_key(func, args, kwargs)
                if cached_val := app_cache.get(key):
                    return cached_val
                result = await func(*args, **kwargs)
                app_cache.set(key, result, ttl)
                return result
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                key = _make_cache_key(func, args, kwargs)
                if cached_val := app_cache.get(key):
                    return cached_val
                result = func(*args, **kwargs)
                app_cache.set(key, result, ttl)
                return result
            return sync_wrapper

    return decorator
