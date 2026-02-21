"""
Controlador refactorizado para gestión de alumnos.

Demuestra la arquitectura limpia con separación de responsabilidades.
Usa inyección de dependencias y sigue principios SOLID.
"""

from typing import List, Dict, Tuple, Optional, Any
from controllers.base_controller import BaseController
from domain.services.alumno_service import AlumnoService
from infrastructure.dtos import AlumnoDTO


class AlumnoControllerRefactorizado(BaseController):
    """
    Controlador refactorizado para gestión de alumnos.
    
    Este controlador demuestra la nueva arquitectura limpia:
    - Inyección de dependencias: El servicio se pasa en el constructor
    - Sin acceso directo a clientes API: Todo pasa por el servicio
    - Sin lógica de negocio: Solo orquestación
    - Métodos documentados con docstrings completos
    
    Attributes:
        service: Servicio inyectado con lógica de negocio
        
    Example:
        >>> service = AlumnoService(repository)
        >>> controller = AlumnoControllerRefactorizado(service)
        >>> alumnos = controller.obtener_alumnos_para_combobox()
    """
    
    def __init__(self, service: AlumnoService):
        """
        Inicializar controlador con servicio inyectado.
        
        Args:
            service: Servicio de dominio para alumnos
        """
        super().__init__()
        self.service = service
    
    # ==================== BÚSQUEDA Y LISTADO ====================
    
    def obtener_alumnos_para_combobox(self) -> List[str]:
        """
        Obtener nombres completos de alumnos activos para combobox.
        
        Retorna: Lista de nombres completos ordenados alfabéticamente,
        listos para mostrar en controles de selección (combobox, dropdown).
        
        Returns:
            List[str]: Nombres de alumnos en formato "Apellido, Nombres"
            
        Raises:
            Cualquier excepción del servicio se captura y retorna lista vacía
            
        Example:
            >>> nombres = controller.obtener_alumnos_para_combobox()
            >>> combobox.options = nombres
            >>> # ['García López, Juan', 'Pérez García, María', ...]
        """
        try:
            alumnos = self.service.obtener_alumnos_activos()
            # Retornar en formato corto (Apellido, Nombres) para combobox
            return [a.nombre_corto for a in alumnos]
        except Exception as e:
            self._handle_error(e, "obtener alumnos para combobox")
            return []
    
    def buscar_alumnos(self, texto: str) -> List[Dict[str, Any]]:
        """
        Buscar alumnos por nombre, DNI o código de matrícula.
        
        Realiza búsqueda flexible que busca coincidencias en:
        - Nombre completo
        - DNI
        - Código de matrícula
        
        Validaciones:
        - Texto debe tener al menos 2 caracteres
        - Búsqueda insensible a mayúsculas
        
        Args:
            texto: Término de búsqueda
            
        Returns:
            List[Dict[str, Any]]: Lista de alumnos encontrados en formato diccionario
                Contiene: id, nombres, apell_paterno, apell_materno, 
                codigo_matricula, grupo, nombre_completo
                
        Example:
            >>> resultados = controller.buscar_alumnos("juan")
            >>> for alumno in resultados:
            ...     print(f"{alumno['nombre_completo']} ({alumno['dni']})")
        """
        try:
            if not texto or len(texto.strip()) < 2:
                self._log_operacion(f"Búsqueda muy corta: '{texto}'", nivel="debug")
                return []
            
            alumnos = self.service.buscar_alumnos(texto)
            self._log_operacion(f"Búsqueda '{texto}': {len(alumnos)} resultados")
            
            return [self._alumno_dto_a_dict(a) for a in alumnos]
        except Exception as e:
            self._handle_error(e, f"buscar alumnos por '{texto}'")
            return []
    
    def obtener_alumnos_por_grupo(self, grupo: str) -> List[Dict[str, Any]]:
        """
        Obtener alumnos activos de un grupo específico.
        
        Args:
            grupo: Letra del grupo (A, B, C, D, E, F, etc.)
            
        Returns:
            List[Dict[str, Any]]: Alumnos del grupo ordenados alfabéticamente
            
        Example:
            >>> alumnos_grupo_a = controller.obtener_alumnos_por_grupo("A")
            >>> print(f"Alumnos en grupo A: {len(alumnos_grupo_a)}")
        """
        try:
            alumnos = self.service.obtener_alumnos_por_grupo(grupo)
            return [self._alumno_dto_a_dict(a) for a in alumnos]
        except Exception as e:
            self._handle_error(e, f"obtener alumnos del grupo {grupo}")
            return []
    
    # ==================== OPERACIONES CRUD ====================
    
    def crear_alumno(self, datos: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict]]:
        """
        Crear nuevo alumno en el sistema.
        
        Realiza validaciones de datos antes de crear:
        1. Valida estructura de datos usando el servicio
        2. Si es válido, delega la creación al repositorio
        3. Retorna resultado con datos del alumno creado
        
        Args:
            datos: Diccionario con información del alumno
                Campos requeridos: nombres, apell_paterno, dni, grupo
                Campos opcionales: apell_materno, carrera, costo_matricula, etc.
                
        Returns:
            Tuple[bool, str, Optional[Dict]]: 
            - (True, "Mensaje de éxito", Datos del alumno creado) si tiene éxito
            - (False, "Mensaje de error", None) si falla
            
        Example:
            >>> exito, msg, alumno = controller.crear_alumno({
            ...     "nombres": "Juan",
            ...     "apell_paterno": "Pérez",
            ...     "apell_materno": "García",
            ...     "dni": "12345678",
            ...     "grupo": "A"
            ... })
            >>> if exito:
            ...     print(f"Alumno creado: {alumno['nombres']}")
            >>> else:
            ...     print(f"Error: {msg}")
        """
        try:
            # 1. Validar datos
            valido, msg_error, campo_error = self.service.validar_datos_alumno(datos)
            if not valido:
                self._log_operacion(f"Validación falló en campo '{campo_error}': {msg_error}")
                return False, msg_error, None
            
            # 2. Crear alumno
            exito, resultado = self.service.repository.crear(datos)
            
            if exito:
                alumno_dict = self._alumno_dto_a_dict(resultado)
                self._log_operacion(f"Alumno creado: {resultado.nombre_completo}")
                return True, "Alumno creado exitosamente", alumno_dict
            else:
                self._log_operacion(f"Error al crear alumno: {resultado}", nivel="error")
                return False, resultado, None
        except Exception as e:
            return self._handle_error(e, "crear alumno") + (None,)
    
    def actualizar_alumno(self, id: int, datos: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict]]:
        """
        Actualizar información de un alumno existente.
        
        Args:
            id: ID del alumno a actualizar
            datos: Diccionario con campos a actualizar
            
        Returns:
            Tuple[bool, str, Optional[Dict]]: (Éxito, Mensaje, Datos actualizados)
            
        Example:
            >>> exito, msg, alumno = controller.actualizar_alumno(1, {
            ...     "apell_paterno": "Nuevo Apellido"
            ... })
        """
        try:
            exito, resultado = self.service.repository.actualizar(id, datos)
            
            if exito:
                alumno_dict = self._alumno_dto_a_dict(resultado)
                self._log_operacion(f"Alumno {id} actualizado")
                return True, "Alumno actualizado correctamente", alumno_dict
            else:
                return False, resultado, None
        except Exception as e:
            return self._handle_error(e, f"actualizar alumno {id}") + (None,)
    
    def eliminar_alumno(self, id: int) -> Tuple[bool, str]:
        """
        Eliminar (desactivar) un alumno del sistema.
        
        En el sistema, "eliminar" significa marcar como inactivo,
        no eliminar datos de la BD.
        
        Args:
            id: ID del alumno a eliminar
            
        Returns:
            Tuple[bool, str]: (Éxito, Mensaje de confirmación o error)
            
        Example:
            >>> exito, msg = controller.eliminar_alumno(5)
            >>> if exito:
            ...     print("Alumno eliminado correctamente")
        """
        try:
            exito, mensaje = self.service.repository.eliminar(id)
            
            if exito:
                self._log_operacion(f"Alumno {id} eliminado")
            else:
                self._log_operacion(f"Error al eliminar alumno {id}: {mensaje}", nivel="error")
            
            return exito, mensaje
        except Exception as e:
            return self._handle_error(e, f"eliminar alumno {id}")
    
    # ==================== OPERACIONES DE NEGOCIO ====================
    
    def obtener_estado_pago(self, costo: float, pagado: float) -> Dict[str, Any]:
        """
        Obtener estado de pago de matrícula de un alumno.
        
        Calcula:
        - Deuda pendiente
        - Porcentaje pagado
        - Estado (completo, parcial, no pagado)
        
        Args:
            costo: Costo total de la matrícula
            pagado: Monto ya pagado
            
        Returns:
            Dict[str, Any]: Información de pago con estructura:
                {
                    "costo": float,
                    "pagado": float,
                    "deuda": float,
                    "porcentaje_pagado": float,
                    "estado": "COMPLETO|PARCIAL|NO_PAGADO"
                }
                
        Example:
            >>> estado = controller.obtener_estado_pago(1000.0, 500.0)
            >>> print(f"Deuda: S/. {estado['deuda']}")
            >>> print(f"Estado: {estado['estado']}")
        """
        try:
            deuda = self.service.calcular_deuda(costo, pagado)
            pct = self.service.obtener_porcentaje_pago(costo, pagado)
            
            if costo <= 0:
                estado = "NO_ESPECIFICADO"
            elif deuda == 0:
                estado = "COMPLETO"
            elif pagado == 0:
                estado = "NO_PAGADO"
            else:
                estado = "PARCIAL"
            
            return {
                "costo": costo,
                "pagado": pagado,
                "deuda": deuda,
                "porcentaje_pagado": pct,
                "estado": estado
            }
        except Exception as e:
            self._handle_error(e, "calcular estado de pago")
            return {
                "costo": costo,
                "pagado": pagado,
                "deuda": costo,
                "porcentaje_pagado": 0.0,
                "estado": "ERROR"
            }
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtener estadísticas generales del estudiantado.
        
        Calcula:
        - Total de alumnos activos e inactivos
        - Distribución por grupos
        - Distribución por modalidad
        
        Returns:
            Dict[str, Any]: Estadísticas generales
            
        Example:
            >>> stats = controller.obtener_estadisticas()
            >>> print(f"Total alumnos: {stats['total_activos']}")
            >>> print(stats['por_grupo'])
            {'A': 30, 'B': 28, 'C': 25}
        """
        try:
            return self.service.obtener_estadisticas()
        except Exception as e:
            self._handle_error(e, "obtener estadísticas")
            return {
                "total_activos": 0,
                "total_inactivos": 0,
                "por_grupo": {},
                "por_modalidad": {}
            }
    
    # ==================== MÉTODOS PRIVADOS ====================
    
    @staticmethod
    def _alumno_dto_a_dict(dto: AlumnoDTO) -> Dict[str, Any]:
        """
        Convertir DTO de alumno a diccionario para retornar a la UI.
        
        Args:
            dto: AlumnoDTO a convertir
            
        Returns:
            Dict[str, Any]: Diccionario con datos del alumno
        """
        return {
            "id": dto.id,
            "nombres": dto.nombres,
            "apell_paterno": dto.apell_paterno,
            "apell_materno": dto.apell_materno,
            "codigo_matricula": dto.codigo_matricula,
            "dni": dto.dni,
            "grupo": dto.grupo,
            "modalidad": dto.modalidad,
            "horario": dto.horario,
            "activo": dto.activo,
            "nombre_completo": dto.nombre_completo,
            "nombre_corto": dto.nombre_corto
        }
