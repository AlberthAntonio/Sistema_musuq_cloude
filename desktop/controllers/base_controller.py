"""
Controlador base para todos los controladores de aplicación.

Define la interfaz común y proporciona utilidades compartidas
para manejo de errores, logging, y orquestación.
"""

from abc import ABC
from typing import Optional, Tuple, Any
import logging


class BaseController(ABC):
    """
    Clase base abstracta para todos los controladores de aplicación.
    
    Los controladores orquestan las operaciones entre la interfaz de usuario
    y los servicios de dominio. No contienen lógica de negocio, solo
    coordinación de operaciones.
    
    Attributes:
        logger: Logger para registrar operaciones
        
    Example:
        >>> class MiController(BaseController):
        ...     def obtener_datos(self):
        ...         # Código del controlador
        ...         pass
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Inicializar controlador base.
        
        Args:
            logger: Logger personalizado (opcional, usa logging por defecto)
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
    
    def _handle_error(self, error: Exception, operacion: str = "") -> Tuple[bool, str]:
        """
        Manejo centralizado de errores.
        
        Registra el error y retorna un resultado estandarizado.
        
        Args:
            error: Excepción capturada
            operacion: Descripción de la operación que falló
            
        Returns:
            Tuple[bool, str]: (Éxito=False, Mensaje de error)
            
        Example:
            >>> try:
            ...     self.hacer_algo()
            ... except Exception as e:
            ...     return self._handle_error(e, "hacer algo importante")
        """
        mensaje_error = str(error)
        
        if operacion:
            mensaje_error = f"Error al {operacion}: {mensaje_error}"
        
        self.logger.error(mensaje_error)
        return False, mensaje_error
    
    def _log_operacion(self, mensaje: str, nivel: str = "info") -> None:
        """
        Registrar operación en el log.
        
        Args:
            mensaje: Mensaje a registrar
            nivel: Nivel de log (debug, info, warning, error)
            
        Example:
            >>> self._log_operacion("Creando nuevo alumno", nivel="info")
        """
        if hasattr(self.logger, nivel):
            getattr(self.logger, nivel)(mensaje)
        else:
            self.logger.info(mensaje)
