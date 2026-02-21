"""
Base abstracta para todos los clientes API.

Este módulo define la interfaz y comportamientos comunes para todos
los clientes que se comunican con la API del backend.

Ejemplo:
    >>> client = BaseAPIClient()
    >>> response = client._parse_response({"items": [...]})
"""

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Optional, List, Union


class BaseAPIClient(ABC):
    """
    Clase abstracta base para todos los clientes de API.
    
    Define la interfaz común y proporciona métodos de utilidad
    para normalizar respuestas de la API.
    
    Attributes:
        token (str): Token de autenticación JWT/Bearer
        base_url (str): URL base de la API
        endpoint (str): Endpoint específico del recurso
        
    Example:
        >>> class MiClient(BaseAPIClient):
        ...     def build_headers(self):
        ...         return {"Authorization": f"Bearer {self.token}"}
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Inicializar cliente base.
        
        Args:
            token: Token de autenticación (opcional, puede asignarse después)
        """
        self.token = token
        self.base_url: Optional[str] = None
        self.endpoint: Optional[str] = None
    
    @abstractmethod
    def build_headers(self) -> Dict[str, str]:
        """
        Construir headers HTTP incluyendo autenticación.
        
        Debe incluir:
        - Content-Type application/json
        - Authorization header con el token
        
        Returns:
            Dict[str, str]: Headers HTTP para usar en requests
            
        Example:
            >>> headers = client.build_headers()
            >>> headers["Authorization"]
            'Bearer eyJhbGc...'
        """
        pass
    
    @abstractmethod
    def _get(self, *args, **kwargs) -> Tuple[bool, Any]:
        """
        Realizar request GET.
        
        Args:
            *args: Argumentos posicionales (ruta, parámetros, etc.)
            **kwargs: Argumentos nombrados (limit, offset, filtros, etc.)
            
        Returns:
            Tuple[bool, Any]: (Éxito de operación, Resultado o error)
            
        Example:
            >>> success, result = client._get("endpoint", limit=100)
            >>> if success:
            ...     print(result)
        """
        pass
    
    @abstractmethod
    def _post(self, *args, **kwargs) -> Tuple[bool, Any]:
        """
        Realizar request POST.
        
        Args:
            *args: Argumentos posicionales (ruta, body, etc.)
            **kwargs: Argumentos nombrados (data, headers, etc.)
            
        Returns:
            Tuple[bool, Any]: (Éxito de operación, Resultado o mensaje de error)
            
        Example:
            >>> success, result = client._post("endpoint", data={"nombre": "Juan"})
        """
        pass
    
    @abstractmethod
    def _put(self, *args, **kwargs) -> Tuple[bool, Any]:
        """
        Realizar request PUT.
        
        Args:
            *args: Argumentos posicionales (ID, ruta, etc.)
            **kwargs: Argumentos nombrados (data, etc.)
            
        Returns:
            Tuple[bool, Any]: (Éxito de operación, Resultado o mensaje de error)
        """
        pass
    
    @abstractmethod
    def _delete(self, *args, **kwargs) -> Tuple[bool, Any]:
        """
        Realizar request DELETE.
        
        Args:
            *args: Argumentos posicionales (ID, ruta, etc.)
            **kwargs: Argumentos nombrados (params, etc.)
            
        Returns:
            Tuple[bool, Any]: (Éxito de operación, Mensaje de confirmación o error)
        """
        pass
    
    @staticmethod
    def _parse_response(response: Union[Dict[str, Any], List[Any]]) -> List[Any]:
        """
        Normalizar respuesta de API a formato consistente.
        
        Convierte respuestas en dos formatos:
        1. Lista directa: [item1, item2, ...] → devuelve igual
        2. Objeto con items: {"items": [...]} → extrae items
        3. Otros formatos: devuelve lista vacía
        
        Args:
            response: Respuesta de la API (dict o list)
            
        Returns:
            List[Any]: Lista de items siempre, incluso si está vacía
            
        Example:
            >>> # Respuesta formato 1:
            >>> items = BaseAPIClient._parse_response([{"id": 1}])
            >>> items
            [{"id": 1}]
            
            >>> # Respuesta formato 2:
            >>> items = BaseAPIClient._parse_response({"items": [{"id": 1}]})
            >>> items
            [{"id": 1}]
            
            >>> # Respuesta inválida:
            >>> items = BaseAPIClient._parse_response({"data": []})
            >>> items
            []
        """
        if isinstance(response, list):
            return response
        
        if isinstance(response, dict):
            return response.get("items", response.get("data", []))
        
        return []
    
    def set_token(self, token: str) -> None:
        """
        Establecer token de autenticación.
        
        Args:
            token: Token JWT/Bearer
            
        Example:
            >>> client.set_token("eyJhbGc...")
        """
        self.token = token
    
    def clear_token(self) -> None:
        """
        Limpiar token de autenticación.
        
        Usar cuando se hace logout del usuario.
        """
        self.token = None
    
    def is_authenticated(self) -> bool:
        """
        Verificar si el cliente tiene token de autenticación.
        
        Returns:
            bool: True si hay token, False si no
        """
        return self.token is not None and len(self.token) > 0
