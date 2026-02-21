"""
Modelo de Pago.
"""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Pago(Base):
    """Modelo de pago de alumno."""
    
    __tablename__ = "pagos"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con alumno
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), nullable=False, index=True)
    
    # Información del pago
    monto = Column(Float, nullable=False)
    fecha = Column(Date, nullable=False, index=True)
    concepto = Column(String(200), nullable=True)  # "Adelanto mensualidad", "Matrícula", etc.
    
    # Timestamps
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relación
    alumno = relationship("Alumno", back_populates="pagos")
    
    def __repr__(self):
        return f"<Pago alumno={self.alumno_id} monto={self.monto} fecha={self.fecha}>"
