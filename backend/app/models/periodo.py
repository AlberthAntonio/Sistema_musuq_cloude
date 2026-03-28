"""
Modelo de Periodo Académico.
Representa un ciclo escolar o académico (ej: "2026-I", "Verano 2026").
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class PeriodoAcademico(Base):
    """Modelo de periodo académico del sistema."""
    
    __tablename__ = "periodos_academicos"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identificación del periodo
    nombre = Column(String(100), nullable=False, unique=True)  # "2026-I", "Verano 2026"
    tipo = Column(String(20), nullable=False)  # 'colegio' o 'academia'
    
    # Rango de fechas
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    
    # Estado del periodo
    estado = Column(String(20), nullable=False, default="activo")  # 'activo', 'cerrado'
    
    # Auditoría
    creado_por = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    
    # Timestamps
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    matriculas = relationship("Matricula", back_populates="periodo", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PeriodoAcademico {self.nombre} ({self.estado})>"
