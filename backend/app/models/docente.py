"""
Modelo de Docente.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Docente(Base):
    """Modelo de docente."""
    
    __tablename__ = "docentes"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Datos personales
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    dni = Column(String(20), unique=True, nullable=True, index=True)
    
    # Contacto
    celular = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    
    # Profesional
    especialidad = Column(String(100), nullable=True)
    
    # Estado
    activo = Column(Boolean, default=True)
    
    # Timestamps
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    horarios = relationship("Horario", back_populates="docente", cascade="all, delete-orphan")
    
    @property
    def nombre_completo(self) -> str:
        return f"{self.apellidos} {self.nombres}"
    
    def __repr__(self):
        return f"<Docente {self.nombre_completo}>"
