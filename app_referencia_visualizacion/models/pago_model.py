from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import date

class Pago(Base):
    __tablename__ = "pagos"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con el alumno (Foreign Key)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), nullable=False)
    
    monto = Column(Float, nullable=False)
    fecha = Column(Date, default=date.today)
    concepto = Column(String, nullable=True) # Ej: "Adelanto mensualidad", "Matrícula", etc.

    # Para poder acceder a los datos del alumno desde el pago
    alumno = relationship("Alumno", back_populates="pagos")