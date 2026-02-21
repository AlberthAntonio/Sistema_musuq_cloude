# app/models/docente_model.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Docente(Base):
    __tablename__ = "docentes"
    
    id = Column(Integer, primary_key=True, index=True)
    nombres = Column(String, nullable=False)
    apellidos = Column(String, nullable=False)
    dni = Column(String(8), unique=True, nullable=True)
    celular = Column(String(15), nullable=True)
    email = Column(String(100), nullable=True)
    especialidad = Column(String(100), nullable=True)
    
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now)
    
    # Relación con horarios
    horarios = relationship("Horario", back_populates="docente", cascade="all, delete-orphan")
    
    @property
    def nombre_completo(self):
        return f"{self.apellidos} {self.nombres}"
    
    def __repr__(self):
        return f"<Docente {self.nombre_completo}>"
