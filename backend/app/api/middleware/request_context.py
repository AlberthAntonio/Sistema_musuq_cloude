import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import request_id_var

class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware de observabilidad y hardening.
    Inyecta un X-Request-Id en el contexto global de Python (contextvars)
    para poder trazar logs desde cualquier punto (servicios, repositorios) 
    sin pasar explícitamente el 'request_id' por las funciones.
    """
    async def dispatch(self, request: Request, call_next):
        # 1. Capturar o generar ID único para toda la traza (Observabilidad)
        request_id = (
            request.headers.get("X-Request-ID")
            or request.headers.get("X-Request-Id")
            or str(uuid.uuid4())
        )
        request.state.request_id = request_id
        
        # Inyectarlo al contexto global para el logger
        token = request_id_var.set(request_id)
        
        start_time = time.time()
        
        try:
            # Continuar con la pila HTTP
            response = await call_next(request)
            
            # Devolver tiempos de procesamiento y Trazabilidad al cliente
            process_time = time.time() - start_time
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
        finally:
            # Limpiar contexto de memoria (evitar memory leaks en contextvars)
            request_id_var.reset(token)
