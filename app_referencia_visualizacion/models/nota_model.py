from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Nota(Base):
    __tablename__ = "notas"

    id = Column(Integer, primary_key=True, index=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), nullable=False)

    sesion_id = Column(Integer, ForeignKey("sesiones_examen.id"), nullable=False)
    
    curso_nombre = Column(String, nullable=False) # Ej: "Aritmética"
    valor = Column(Float, nullable=False)         # Ej: 15.0
    
    alumno = relationship("Alumno", back_populates="notas")
    sesion = relationship("SesionExamen", back_populates="notas")