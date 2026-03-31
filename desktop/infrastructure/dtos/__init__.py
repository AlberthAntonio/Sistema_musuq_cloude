"""
Data Transfer Object para Alumno.

Define la estructura de datos que fluye entre capas de la aplicación.
Centraliza la conversión de datos desde la API.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class AlumnoDTO:
    """
    Data Transfer Object para representar un Alumno.
    
    Los DTOs son objetos simples que transportan datos entre capas
    sin contener lógica de negocio.
    
    Attributes:
        id: Identificador único del alumno
        codigo_matricula: Código de matrícula asignado por la institución
        dni: Documento Nacional de Identidad (8 dígitos)
        nombres: Nombres del alumno
        apell_paterno: Apellido paterno
        apell_materno: Apellido materno
        grupo: Grupo/sección de estudio (A, B, C, D, etc.)
        modalidad: Modalidad de estudio (presencial, virtual, híbrida)
        horario: Horario de estudio del alumno (MATUTINO, VESPERTINO, DOBLE HORARIO)
        activo: Estado del alumno (True = activo, False = inactivo/retirado)
        
    Example:
        >>> alumno = AlumnoDTO(
        ...     id=1,
        ...     nombres="Juan",
        ...     apell_paterno="Pérez",
        ...     dni="12345678"
        ... )
        >>> print(alumno.nombre_completo)
        'Pérez Juan'
    """
    
    id: int
    codigo_matricula: str
    dni: str
    nombres: str
    apell_paterno: str
    apell_materno: str
    grupo: str
    modalidad: str
    horario: str
    tiene_foto: bool = False
    activo: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlumnoDTO':
        """
        Factory method para crear AlumnoDTO desde diccionario de API.
        
        Mapea automáticamente los campos de la respuesta API a los atributos
        del DTO, utilizando valores por defecto para campos faltantes.
        
        Args:
            data: Diccionario con datos de alumno desde la API
            
        Returns:
            AlumnoDTO: Objeto DTO completamente inicializado
            
        Example:
            >>> api_response = {
            ...     "id": 1,
            ...     "nombres": "Juan",
            ...     "apell_paterno": "Pérez",
            ...     "dni": "12345678"
            ... }
            >>> alumno = AlumnoDTO.from_dict(api_response)
            >>> alumno.id
            1
        """
        return cls(
            id=data.get("id", 0),
            codigo_matricula=data.get("codigo_matricula", ""),
            dni=data.get("dni", ""),
            nombres=data.get("nombres", ""),
            apell_paterno=data.get("apell_paterno", ""),
            apell_materno=data.get("apell_materno", ""),
            grupo=data.get("grupo", ""),
            modalidad=data.get("modalidad", ""),
            horario=data.get("horario", ""),
            tiene_foto=data.get("tiene_foto", False),
            activo=data.get("activo", True)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertir DTO a diccionario.
        
        Útil para serializar o pasar a otras partes de la aplicación
        que esperan diccionarios.
        
        Returns:
            Dict[str, Any]: Representación en diccionario del alumno
            
        Example:
            >>> alumno_dict = alumno.to_dict()
            >>> alumno_dict["id"]
            1
        """
        return {
            "id": self.id,
            "codigo_matricula": self.codigo_matricula,
            "dni": self.dni,
            "nombres": self.nombres,
            "apell_paterno": self.apell_paterno,
            "apell_materno": self.apell_materno,
            "grupo": self.grupo,
            "modalidad": self.modalidad,
            "horario": self.horario,
            "tiene_foto": self.tiene_foto,
            "activo": self.activo
        }
    
    @property
    def nombre_completo(self) -> str:
        """
        Propiedad computada que retorna el nombre completo formateado.
        
        Retorna el nombre en formato: "Apellido Paterno Apellido Materno Nombres"
        Elimina espacios extra.
        
        Returns:
            str: Nombre completo del alumno
            
        Example:
            >>> alumno.nombre_completo
            'Pérez García Juan'
        """
        partes = [self.apell_paterno, self.apell_materno, self.nombres]
        return " ".join(p for p in partes if p).strip()
    
    @property
    def nombre_corto(self) -> str:
        """
        Propiedad computada que retorna un nombre abreviado.
        
        Retorna: "Apellido, Nombres"
        
        Returns:
            str: Nombre en formato corto
            
        Example:
            >>> alumno.nombre_corto
            'Pérez García, Juan'
        """
        apellido = f"{self.apell_paterno} {self.apell_materno}".strip()
        return f"{apellido}, {self.nombres}".strip()
    
    def __str__(self) -> str:
        """
        Representación en string del DTO.
        
        Returns:
            str: Nombre completo del alumno
        """
        return self.nombre_completo
    
    def __repr__(self) -> str:
        """
        Representación técnica para debugging.
        
        Returns:
            str: Representación debug del objeto
        """
        return f"AlumnoDTO(id={self.id}, nombres='{self.nombres}', dni='{self.dni}')"


@dataclass
class CursoDTO:
    """
    Data Transfer Object para representar un Curso.
    
    Attributes:
        id: Identificador único del curso
        nombre: Nombre del curso
        codigo: Código del curso (ej: MAT-101)
        descripcion: Descripción o contenido del curso
        creditos: Número de créditos del curso
        horas_teoricas: Horas de teoría por semana
        horas_practicas: Horas de práctica por semana
    """
    
    id: int
    nombre: str
    codigo: str = ""
    descripcion: str = ""
    creditos: int = 0
    horas_teoricas: int = 0
    horas_practicas: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CursoDTO':
        """
        Factory method para crear CursoDTO desde diccionario de API.
        
        Args:
            data: Diccionario con datos de curso desde la API
            
        Returns:
            CursoDTO: Objeto DTO completamente inicializado
        """
        return cls(
            id=data.get("id", 0),
            nombre=data.get("nombre", ""),
            codigo=data.get("codigo", ""),
            descripcion=data.get("descripcion", ""),
            creditos=data.get("creditos", 0),
            horas_teoricas=data.get("horas_teoricas", 0),
            horas_practicas=data.get("horas_practicas", 0)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertir DTO a diccionario.
        
        Returns:
            Dict[str, Any]: Representación en diccionario del curso
        """
        return {
            "id": self.id,
            "nombre": self.nombre,
            "codigo": self.codigo,
            "descripcion": self.descripcion,
            "creditos": self.creditos,
            "horas_teoricas": self.horas_teoricas,
            "horas_practicas": self.horas_practicas
        }


@dataclass
class HorarioDTO:
    """
    Data Transfer Object para representar un Bloque de Horario.
    
    Attributes:
        id: Identificador único del horario
        grupo: Grupo/sección (A, B, C, D)
        dia: Día de la semana (1=Lunes ... 5=Viernes)
        hora_inicio: Hora de inicio (formato HH:MM)
        hora_fin: Hora de fin (formato HH:MM)
        curso_id: ID del curso asignado
        nombre_curso: Nombre del curso
        docente_id: ID del docente
        nombre_docente: Nombre del docente
        aula: Número o nombre del aula
    """
    
    id: int
    grupo: str
    dia: int
    hora_inicio: str
    hora_fin: str
    curso_id: int = 0
    nombre_curso: str = ""
    docente_id: int = 0
    nombre_docente: str = ""
    aula: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HorarioDTO':
        """
        Factory method para crear HorarioDTO desde diccionario de API.
        
        Args:
            data: Diccionario con datos de horario desde la API
            
        Returns:
            HorarioDTO: Objeto DTO completamente inicializado
        """
        return cls(
            id=data.get("id", 0),
            grupo=data.get("grupo", ""),
            dia=data.get("dia", 1),
            hora_inicio=data.get("hora_inicio", ""),
            hora_fin=data.get("hora_fin", ""),
            curso_id=data.get("curso_id", 0),
            nombre_curso=data.get("nombre_curso", data.get("curso", "")),
            docente_id=data.get("docente_id", 0),
            nombre_docente=data.get("nombre_docente", data.get("docente", "")),
            aula=data.get("aula", "")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertir DTO a diccionario.
        
        Returns:
            Dict[str, Any]: Representación en diccionario del horario
        """
        return {
            "id": self.id,
            "grupo": self.grupo,
            "dia": self.dia,
            "hora_inicio": self.hora_inicio,
            "hora_fin": self.hora_fin,
            "curso_id": self.curso_id,
            "nombre_curso": self.nombre_curso,
            "docente_id": self.docente_id,
            "nombre_docente": self.nombre_docente,
            "aula": self.aula
        }
