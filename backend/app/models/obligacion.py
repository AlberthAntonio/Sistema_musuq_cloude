"""
Modelo de Obligación de Pago.
Representa una deuda específica ligada a una matrícula (mensualidad, matrícula, etc).
"""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class ObligacionPago(Base):
    """Modelo de obligación de pago vinculada a una matrícula."""
    
    __tablename__ = "obligaciones_pago"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con matrícula
    matricula_id = Column(Integer, ForeignKey("matriculas.id"), nullable=False, index=True)
    
    # Detalle de la obligación
    concepto = Column(String(200), nullable=False)  # "Matrícula", "Mensualidad Marzo", etc.
    monto_total = Column(Float, nullable=False)
    monto_pagado = Column(Float, nullable=False, default=0.0)
    fecha_vencimiento = Column(Date, nullable=True)
    
    # Estado calculado
    estado = Column(String(20), nullable=False, default="pendiente")  # 'pendiente', 'parcial', 'pagado'
    
    # Timestamps
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Auditoría
    creado_por = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    
    # Relaciones ORM
    matricula = relationship("Matricula", back_populates="obligaciones")
    pagos = relationship("Pago", back_populates="obligacion", cascade="all, delete-orphan")
    
    @property
    def saldo_pendiente(self) -> float:
        """Calcula el saldo pendiente de la obligación."""
        return max(0.0, self.monto_total - self.monto_pagado)
    
    def actualizar_estado(self):
        """Recalcula el estado según monto_pagado vs monto_total."""
        if self.monto_pagado >= self.monto_total:
            self.estado = "pagado"
        elif self.monto_pagado > 0:
            self.estado = "parcial"
        else:
            self.estado = "pendiente"
    
    def __repr__(self):
        return f"<ObligacionPago {self.concepto} total={self.monto_total} pagado={self.monto_pagado}>"
