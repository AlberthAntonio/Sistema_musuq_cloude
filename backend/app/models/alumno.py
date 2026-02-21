"""
Modelo de Alumno - Adaptado del sistema original.
"""
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Alumno(Base):
    """Modelo de alumno del sistema."""
    
    __tablename__ = "alumnos"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Código de matrícula único generado (ej: POA250001)
    codigo_matricula = Column(String(20), unique=True, nullable=False, index=True)
    
    # Datos personales
    dni = Column(String(20), unique=True, index=True, nullable=False)
    nombres = Column(String(100), nullable=False)
    apell_paterno = Column(String(50), nullable=False)
    apell_materno = Column(String(50), nullable=False)
    fecha_nacimiento = Column(Date, nullable=True)
    
    # Datos académicos
    grupo = Column(String(10), nullable=True)  # A, B, C, D
    carrera = Column(String(100), nullable=True)  # Medicina, Ing...
    modalidad = Column(String(50), nullable=True)  # Ordinario, Primera Opción...
    horario = Column(String(50), nullable=True)  # MATUTINO, VESPERTINO, DOBLE HORARIO
    grado = Column(String(20), nullable=True)  # Para modalidad COLEGIO: 1ro, 2do, etc.
    
    # Datos de padres/apoderados
    nombre_padre_completo = Column(String(150), nullable=True)
    celular_padre_1 = Column(String(20), nullable=True)
    celular_padre_2 = Column(String(20), nullable=True)
    descripcion = Column(Text, nullable=True)
    
    # Datos económicos
    costo_matricula = Column(Float, default=0.0)
    
    # Estado
    activo = Column(Boolean, default=True)
    
    # Timestamps
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    asistencias = relationship("Asistencia", back_populates="alumno", cascade="all, delete-orphan")
    pagos = relationship("Pago", back_populates="alumno", cascade="all, delete-orphan")
    notas = relationship("Nota", back_populates="alumno", cascade="all, delete-orphan")
    
    @property
    def nombre_completo(self) -> str:
        return f"{self.apell_paterno} {self.apell_materno}, {self.nombres}"
    
    def __repr__(self):
        return f"<Alumno {self.codigo_matricula}: {self.nombre_completo}>"
