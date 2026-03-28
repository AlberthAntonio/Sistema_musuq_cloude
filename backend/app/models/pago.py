"""
Modelo de Pago.
Ahora vinculado a una ObligacionPago en lugar de directamente al alumno.
"""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Pago(Base):
    """Modelo de pago aplicado a una obligación de pago."""
    
    __tablename__ = "pagos"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con obligación de pago (reemplaza alumno_id)
    obligacion_id = Column(Integer, ForeignKey("obligaciones_pago.id"), nullable=False, index=True)
    
    # Información del pago
    monto = Column(Float, nullable=False)
    fecha = Column(Date, nullable=False, index=True)
    concepto = Column(String(200), nullable=True)  # Nota adicional del pago
    
    # Timestamps
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    
    # Auditoría
    creado_por = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    
    # Relación ORM
    obligacion = relationship("ObligacionPago", back_populates="pagos")
    
    def __repr__(self):
        return f"<Pago obligacion={self.obligacion_id} monto={self.monto} fecha={self.fecha}>"
