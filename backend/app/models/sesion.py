"""
Modelo de Sesión de Examen.
"""
from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class SesionExamen(Base):
    """Modelo de sesión de examen."""
    
    __tablename__ = "sesiones_examen"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Información de la sesión
    fecha = Column(Date, nullable=False, index=True)
    nombre = Column(String(100), nullable=False)  # Ej: "Semanal 1", "Bimestral"
    estado = Column(String(20), default="Abierto")  # Abierto, Cerrado
    
    # Timestamps
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    notas = relationship("Nota", back_populates="sesion", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"{self.fecha} - {self.nombre}"
