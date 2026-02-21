from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import date

class SesionExamen(Base):
    __tablename__ = "sesiones_examen"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, default=date.today)
    nombre = Column(String, nullable=False)  # Ej: "Semanal 1", "Bimestral"
    estado = Column(String, default="Abierto")

    # Relación: Una sesión contiene muchas notas de diferentes alumnos y grupos
    notas = relationship("Nota", back_populates="sesion", cascade="all, delete-orphan")

    def __repr__(self):
        return f"{self.fecha} - {self.nombre}"