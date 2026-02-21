"""
Interfaz base para todos los repositorios.

Define el contrato que deben cumplir todos los repositorios
para acceso a datos consistente.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple


class BaseRepository(ABC):
    """
    Clase abstracta base para todos los repositorios.
    
    Los repositorios actúan como una abstracción sobre la fuente de datos
    (API, BD, archivo, etc.), permitiendo cambiar la implementación sin
    afectar la lógica de negocio.
    
    Esta interfaz define las operaciones CRUD básicas más operaciones
    comunes como búsqueda y filtrado.
    
    Example:
        >>> class AlumnoRepository(BaseRepository):
        ...     def obtener_todos(self):
        ...         # Implementación específica
        ...         pass
    """
    
    @abstractmethod
    def obtener_todos(self, limit: int = 1000) -> List[Any]:
        """
        Obtener todos los elementos del repositorio.
        
        Args:
            limit: Número máximo de elementos a retornar
            
        Returns:
            List[Any]: Lista de elementos, puede estar vacía si no hay datos
            
        Raises:
            Puede lanzar excepciones específicas del repositorio
        """
        pass
    
    @abstractmethod
    def obtener_por_id(self, id: int) -> Optional[Any]:
        """
        Obtener un elemento específico por su ID.
        
        Args:
            id: Identificador único del elemento
            
        Returns:
            Optional[Any]: Elemento si existe, None si no fue encontrado
        """
        pass
    
    @abstractmethod
    def crear(self, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Crear un nuevo elemento en el repositorio.
        
        Args:
            data: Diccionario con los datos del nuevo elemento
            
        Returns:
            Tuple[bool, Any]: (Éxito de la operación, Elemento creado o mensaje de error)
        """
        pass
    
    @abstractmethod
    def actualizar(self, id: int, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Actualizar un elemento existente.
        
        Args:
            id: Identificador del elemento a actualizar
            data: Diccionario con los datos a actualizar
            
        Returns:
            Tuple[bool, Any]: (Éxito de la operación, Elemento actualizado o mensaje de error)
        """
        pass
    
    @abstractmethod
    def eliminar(self, id: int) -> Tuple[bool, str]:
        """
        Eliminar un elemento del repositorio.
        
        Args:
            id: Identificador del elemento a eliminar
            
        Returns:
            Tuple[bool, str]: (Éxito de la operación, Mensaje de confirmación o error)
        """
        pass
    
    @abstractmethod
    def buscar(self, criterio: str) -> List[Any]:
        """
        Buscar elementos que coincidan con un criterio.
        
        Args:
            criterio: Término de búsqueda (formato depende de la implementación)
            
        Returns:
            List[Any]: Elementos que coinciden con la búsqueda
        """
        pass
