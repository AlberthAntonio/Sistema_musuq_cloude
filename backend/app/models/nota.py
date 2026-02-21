"""
Modelo de Nota.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Nota(Base):
    """Modelo de nota de alumno."""
    
    __tablename__ = "notas"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relaciones
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), nullable=False, index=True)
    sesion_id = Column(Integer, ForeignKey("sesiones_examen.id"), nullable=False, index=True)
    
    # Información de la nota
    curso_nombre = Column(String(100), nullable=False)  # Ej: "Aritmética"
    valor = Column(Float, nullable=False)  # Ej: 15.0
    
    # Relaciones
    alumno = relationship("Alumno", back_populates="notas")
    sesion = relationship("SesionExamen", back_populates="notas")
    
    def __repr__(self):
        return f"<Nota alumno={self.alumno_id} curso={self.curso_nombre} valor={self.valor}>"
