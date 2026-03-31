"""
Modelo de Alumno - Solo datos personales.
Los datos académicos y financieros ahora viven en Matricula y ObligacionPago.
"""
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Alumno(Base):
    """Modelo de alumno del sistema - datos personales únicamente."""
    
    __tablename__ = "alumnos"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Datos personales
    dni = Column(String(20), unique=True, index=True, nullable=False)
    nombres = Column(String(100), nullable=False)
    apell_paterno = Column(String(50), nullable=False)
    apell_materno = Column(String(50), nullable=False)
    fecha_nacimiento = Column(Date, nullable=True)
    
    # Datos de padres/apoderados
    nombre_padre_completo = Column(String(150), nullable=True)
    celular_padre_1 = Column(String(20), nullable=True)
    celular_padre_2 = Column(String(20), nullable=True)
    descripcion = Column(Text, nullable=True)
    foto_data = Column(LargeBinary, nullable=True)
    foto_mime_type = Column(String(100), nullable=True)
    
    # Auditoría
    creado_por = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    
    # Estado
    activo = Column(Boolean, default=True)
    
    # Timestamps
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    asistencias = relationship("Asistencia", back_populates="alumno", cascade="all, delete-orphan")
    notas = relationship("Nota", back_populates="alumno", cascade="all, delete-orphan")
    matriculas = relationship("Matricula", back_populates="alumno", cascade="all, delete-orphan")
    
    @property
    def nombre_completo(self) -> str:
        return f"{self.apell_paterno} {self.apell_materno}, {self.nombres}"

    @property
    def codigo_matricula(self):
        """Retorna el código de la matrícula activa del alumno."""
        if not self.matriculas:
            return None
        activas = [m for m in self.matriculas if m.estado == "activo"]
        return activas[0].codigo_matricula if activas else (self.matriculas[0].codigo_matricula if self.matriculas else None)

    @property
    def horario(self):
        """Retorna el horario de la matrícula activa del alumno (MATUTINO, VESPERTINO, DOBLE HORARIO)."""
        if not self.matriculas:
            return None
        activas = [m for m in self.matriculas if m.estado == "activo"]
        m = activas[0] if activas else (self.matriculas[0] if self.matriculas else None)
        return m.horario if m else None

    @property
    def tiene_foto(self) -> bool:
        return bool(self.foto_data)

    def __repr__(self):
        return f"<Alumno {self.dni}: {self.nombre_completo}>"
