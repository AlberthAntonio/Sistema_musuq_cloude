"""
Repositorio para la gestión de datos de Alumnos.

Proporciona abstracción sobre el cliente API para operaciones
con alumnos. Realiza conversiones de datos a DTOs.
"""

from typing import List, Optional, Tuple, Dict, Any
from domain.repositories.base_repository import BaseRepository
from infrastructure.dtos import AlumnoDTO
from core.api_client import AlumnoClient


class AlumnoRepository(BaseRepository):
    """
    Implementación del repositorio para Alumnos.
    
    Actúa como intermediario entre la lógica de negocio y el cliente API,
    manejando la conversión de datos y normalizando respuestas.
    
    Attributes:
        client: Cliente API para alumnos
        
    Example:
        >>> client = AlumnoClient()
        >>> repo = AlumnoRepository(client)
        >>> alumnos = repo.obtener_todos()
    """
    
    def __init__(self, client: AlumnoClient):
        """
        Inicializar repositorio de alumnos.
        
        Args:
            client: Cliente API inyectado para acceso a datos
        """
        self.client = client
    
    def obtener_todos(self, limit: int = 1000) -> List[AlumnoDTO]:
        """
        Obtener todos los alumnos desde la API.
        
        Realiza conversión automática a DTOs para normalizar los datos.
        
        Args:
            limit: Número máximo de alumnos a obtener
            
        Returns:
            List[AlumnoDTO]: Lista de alumnos como DTOs vacía si hay error
            
        Example:
            >>> alumnos = repo.obtener_todos(limit=500)
            >>> print(len(alumnos))
            245
        """
        success, result = self.client.obtener_todos(limit=limit)
        
        if not success:
            return []
        
        # Normalizar respuesta (puede ser lista o dict con "items")
        items = self.client._parse_response(result)
        
        # Convertir cada item a DTO
        return [AlumnoDTO.from_dict(item) for item in items]
    
    def obtener_por_id(self, id: int) -> Optional[AlumnoDTO]:
        """
        Obtener alumno por ID.
        
        Args:
            id: Identificador del alumno
            
        Returns:
            Optional[AlumnoDTO]: DTO del alumno o None si no existe
        """
        success, result = self.client.obtener_por_id(id)
        
        if not success:
            return None
        
        return AlumnoDTO.from_dict(result) if isinstance(result, dict) else None
    
    def obtener_por_grupo(self, grupo: str) -> List[AlumnoDTO]:
        """
        Obtener alumnos filtrados por grupo.
        
        Args:
            grupo: Letra del grupo (A, B, C, D, etc.)
            
        Returns:
            List[AlumnoDTO]: Alumnos del grupo, vacía si no hay o error
        """
        alumnos = self.obtener_todos()
        return [a for a in alumnos if a.grupo == grupo and a.activo]
    
    def obtener_por_grupo_y_modalidad(self, grupo: str, modalidad: str) -> List[AlumnoDTO]:
        """
        Obtener alumnos filtrados por grupo y modalidad.
        
        Args:
            grupo: Letra del grupo
            modalidad: Tipo de modalidad (presencial, virtual, etc.)
            
        Returns:
            List[AlumnoDTO]: Alumnos que coinciden con los criterios
        """
        alumnos = self.obtener_todos()
        return [
            a for a in alumnos 
            if a.grupo == grupo 
            and a.modalidad == modalidad 
            and a.activo
        ]
    
    def buscar(self, texto: str) -> List[AlumnoDTO]:
        """
        Buscar alumnos por texto (nombre, DNI, código).
        
        La búsqueda es insensible a mayúsculas y busca en múltiples campos.
        
        Args:
            texto: Término de búsqueda
            
        Returns:
            List[AlumnoDTO]: Alumnos que coinciden con la búsqueda
            
        Example:
            >>> alumnos = repo.buscar("Juan")
            >>> print(len(alumnos))
            5
        """
        if not texto or len(texto.strip()) < 2:
            return []
        
        success, result = self.client.buscar(texto)
        
        if not success:
            return []
        
        items = self.client._parse_response(result)
        return [AlumnoDTO.from_dict(item) for item in items]
    
    def crear(self, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Crear nuevo alumno en el sistema.
        
        Args:
            data: Diccionario con datos del alumno (nombres, dni, grupo, etc.)
            
        Returns:
            Tuple[bool, Any]: (Éxito, Alumno creado como DTO o mensaje de error)
            
        Example:
            >>> success, alumno = repo.crear({
            ...     "nombres": "Juan",
            ...     "apell_paterno": "Pérez",
            ...     "dni": "12345678",
            ...     "grupo": "A"
            ... })
        """
        success, result = self.client.crear(data)
        
        if success:
            return True, AlumnoDTO.from_dict(result) if isinstance(result, dict) else result
        else:
            error_msg = result.get("error", "Error al crear") if isinstance(result, dict) else str(result)
            return False, error_msg
    
    def actualizar(self, id: int, data: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Actualizar datos de un alumno existente.
        
        Args:
            id: Identificador del alumno
            data: Diccionario con campos a actualizar
            
        Returns:
            Tuple[bool, Any]: (Éxito, Alumno actualizado como DTO o mensaje de error)
        """
        success, result = self.client.actualizar(id, data)
        
        if success:
            return True, AlumnoDTO.from_dict(result) if isinstance(result, dict) else result
        else:
            error_msg = result.get("error", "Error al actualizar") if isinstance(result, dict) else str(result)
            return False, error_msg
    
    def eliminar(self, id: int) -> Tuple[bool, str]:
        """
        Eliminar (marcar como inactivo) un alumno.
        
        Args:
            id: Identificador del alumno a eliminar
            
        Returns:
            Tuple[bool, str]: (Éxito, Mensaje de confirmación o error)
        """
        success, result = self.client.eliminar(id)
        
        if success:
            return True, "Alumno eliminado correctamente"
        else:
            error_msg = result.get("error", "Error al eliminar") if isinstance(result, dict) else str(result)
            return False, error_msg
    
    def contar_activos(self) -> int:
        """
        Contar alumnos activos en el sistema.
        
        Returns:
            int: Cantidad de alumnos activos
        """
        alumnos = self.obtener_todos()
        return len([a for a in alumnos if a.activo])
    
    def contar_por_grupo(self, grupo: str) -> int:
        """
        Contar alumnos activos en un grupo específico.
        
        Args:
            grupo: Letra del grupo
            
        Returns:
            int: Cantidad de alumnos en el grupo
        """
        return len(self.obtener_por_grupo(grupo))
