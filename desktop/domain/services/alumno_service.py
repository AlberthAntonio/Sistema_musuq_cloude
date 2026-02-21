"""
Servicio de dominio para lógica de negocio de Alumnos.

Centraliza la lógica de negocio, validaciones y operaciones
que no son simples acceso a datos.
"""

from typing import List, Tuple, Optional
from domain.repositories.alumno_repository import AlumnoRepository
from infrastructure.dtos import AlumnoDTO


class AlumnoService:
    """
    Servicio de dominio para la gestión de alumnos.
    
    Encapsula toda la lógica de negocio relacionada con alumnos,
    incluyendo validaciones, cálculos y operaciones complejas.
    Delega acceso a datos al repositorio.
    
    Attributes:
        repository: Repositorio inyectado para acceso a datos
        
    Example:
        >>> repo = AlumnoRepository(client)
        >>> service = AlumnoService(repo)
        >>> alumnos = service.obtener_alumnos_activos()
    """
    
    def __init__(self, repository: AlumnoRepository):
        """
        Inicializar servicio de alumnos.
        
        Args:
            repository: Repositorio inyectado para operaciones de datos
        """
        self.repository = repository
    
    def obtener_alumnos_activos(self) -> List[AlumnoDTO]:
        """
        Obtener alumnos activos ordenados alfabéticamente por apellido.
        
        Lógica de negocio: Solo alumnos activos, ordenados por apellido.
        
        Returns:
            List[AlumnoDTO]: Alumnos ordenados: Apellido Paterno, Apellido Materno, Nombres
            
        Example:
            >>> alumnos = service.obtener_alumnos_activos()
            >>> for alumno in alumnos:
            ...     print(alumno.nombre_completo)
        """
        alumnos = self.repository.obtener_todos()
        activos = [a for a in alumnos if a.activo]
        
        # Ordenar por apellido paterno, luego materno, luego nombre
        return sorted(
            activos,
            key=lambda x: (x.apell_paterno.lower(), x.apell_materno.lower(), x.nombres.lower())
        )
    
    def obtener_alumnos_por_grupo(self, grupo: str) -> List[AlumnoDTO]:
        """
        Obtener alumnos activos de un grupo específico.
        
        Args:
            grupo: Letra del grupo (A, B, C, D, etc.)
            
        Returns:
            List[AlumnoDTO]: Alumnos del grupo ordenados alfabéticamente
            
        Example:
            >>> alumnos_a = service.obtener_alumnos_por_grupo("A")
        """
        alumnos = self.repository.obtener_por_grupo(grupo)
        return sorted(
            alumnos,
            key=lambda x: (x.apell_paterno.lower(), x.apell_materno.lower())
        )
    
    def buscar_alumnos(self, texto: str) -> List[AlumnoDTO]:
        """
        Buscar alumnos por nombre, DNI o código de matrícula.
        
        Validaciones:
        - El texto debe tener al menos 2 caracteres
        - La búsqueda es insensible a mayúsculas
        
        Args:
            texto: Término de búsqueda
            
        Returns:
            List[AlumnoDTO]: Alumnos encontrados ordenados alfabéticamente
            
        Example:
            >>> resultados = service.buscar_alumnos("juan")
            >>> print(f"Encontrados: {len(resultados)}")
        """
        if not texto or len(texto.strip()) < 2:
            return []
        
        alumnos = self.repository.buscar(texto.strip())
        return sorted(
            alumnos,
            key=lambda x: x.apell_paterno.lower()
        )
    
    def calcular_deuda(self, costo_matricula: float, monto_pagado: float) -> float:
        """
        Calcular deuda de matrícula de un alumno.
        
        Lógica de negocio:
        - Deuda = Costo - Pagado
        - La deuda no puede ser negativa (mínimo 0)
        
        Args:
            costo_matricula: Costo total de la matrícula
            monto_pagado: Monto ya pagado por el alumno
            
        Returns:
            float: Deuda pendiente (0 si está completamente pagado)
            
        Example:
            >>> deuda = service.calcular_deuda(1000.0, 750.0)
            >>> print(f"Deuda: S/. {deuda}")
            Deuda: S/. 250.0
        """
        return max(0.0, costo_matricula - monto_pagado)
    
    def obtener_porcentaje_pago(self, costo_matricula: float, monto_pagado: float) -> float:
        """
        Calcular porcentaje de pago de matrícula.
        
        Args:
            costo_matricula: Costo total
            monto_pagado: Monto pagado
            
        Returns:
            float: Porcentaje pagado (0-100)
            
        Example:
            >>> pct = service.obtener_porcentaje_pago(1000.0, 500.0)
            >>> print(f"Pagado: {pct}%")
            Pagado: 50.0%
        """
        if costo_matricula <= 0:
            return 0.0
        
        return (monto_pagado / costo_matricula) * 100
    
    def validar_datos_alumno(self, data: dict) -> Tuple[bool, str, Optional[str]]:
        """
        Validar datos de alumno antes de guardar en el sistema.
        
        Validaciones realizadas:
        1. DNI: Debe tener exactamente 8 dígitos
        2. Nombres: Campo requerido, no vacío
        3. Apellido paterno: Campo requerido
        4. Grupo: Debe seleccionar uno
        5. Carrera: Debe seleccionar una
        6. Costo de matrícula: No puede ser negativo
        
        Args:
            data: Diccionario con datos a validar
            
        Returns:
            Tuple[bool, str, Optional[str]]: (Es válido, Mensaje de error, Campo con error)
                - El campo "Campo con error" es None si no hay errores
                
        Example:
            >>> valido, msg, campo = service.validar_datos_alumno({
            ...     "dni": "12345678",
            ...     "nombres": "Juan",
            ...     "apell_paterno": "Pérez"
            ... })
            >>> if not valido:
            ...     print(f"Error en {campo}: {msg}")
        """
        # Validar DNI
        dni = data.get("dni", "").strip()
        if not dni or len(dni) != 8 or not dni.isdigit():
            return False, "DNI debe tener exactamente 8 dígitos", "dni"
        
        # Validar nombre
        if not data.get("nombres", "").strip():
            return False, "Nombres son requeridos", "nombres"
        
        # Validar apellido paterno
        if not data.get("apell_paterno", "").strip():
            return False, "Apellido paterno es requerido", "apell_paterno"
        
        # Validar grupo
        grupo = data.get("grupo", "").strip()
        if not grupo or grupo == "--Seleccione":
            return False, "Debe seleccionar un grupo válido", "grupo"
        
        # Validar carrera (si está presente)
        if "carrera" in data:
            carrera = data.get("carrera", "").strip()
            if not carrera or carrera == "--Seleccione":
                return False, "Debe seleccionar una carrera válida", "carrera"
        
        # Validar costo de matrícula (si está presente)
        if "costo_matricula" in data:
            try:
                costo = float(data.get("costo_matricula") or 0)
                if costo < 0:
                    return False, "Costo no puede ser negativo", "costo_matricula"
            except (ValueError, TypeError):
                return False, "Costo debe ser un número válido", "costo_matricula"
        
        return True, "Datos válidos", None
    
    def obtener_estadisticas(self) -> dict:
        """
        Obtener estadísticas generales del estudiantado.
        
        Calcula:
        - Total de alumnos activos
        - Alumnos por grupo
        - Alumnos por modalidad
        
        Returns:
            dict: Diccionario con estadísticas
            
        Example:
            >>> stats = service.obtener_estadisticas()
            >>> print(f"Total: {stats['total_activos']}")
        """
        alumnos = self.repository.obtener_todos()
        activos = [a for a in alumnos if a.activo]
        
        # Contar por grupo
        por_grupo = {}
        for grupo in ['A', 'B', 'C', 'D', 'E', 'F']:
            por_grupo[grupo] = len([a for a in activos if a.grupo == grupo])
        
        # Contar por modalidad
        por_modalidad = {}
        for alumno in activos:
            modalidad = alumno.modalidad or "Sin especificar"
            por_modalidad[modalidad] = por_modalidad.get(modalidad, 0) + 1
        
        return {
            "total_activos": len(activos),
            "total_inactivos": len([a for a in alumnos if not a.activo]),
            "por_grupo": por_grupo,
            "por_modalidad": por_modalidad
        }
