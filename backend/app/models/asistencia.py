"""
Modelo de Asistencia - Adaptado del sistema original.
"""
from sqlalchemy import Column, Integer, String, Date, Time, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Asistencia(Base):
    """Modelo de registro de asistencia."""
    
    __tablename__ = "asistencias"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relaciones
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), nullable=False, index=True)
    registrado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    # Datos de asistencia
    fecha = Column(Date, nullable=False, index=True)
    hora = Column(Time, nullable=True)
    
    # Estado del registro: PUNTUAL, TARDANZA, FALTA
    estado = Column(String(20), nullable=False, default="Puntual")
    
    # Turno en que ocurrió la asistencia: MAÑANA o TARDE
    # (Distinto de Alumno.horario que es MATUTINO/VESPERTINO/DOBLE HORARIO)
    turno = Column(String(20), nullable=False)
    
    # Alerta de turno cruzado: True si el alumno asistió en un turno distinto al de su horario
    alerta_turno = Column(Boolean, default=False)
    
    # Observaciones
    observacion = Column(Text, nullable=True)
    
    # Timestamp de registro
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    alumno = relationship("Alumno", back_populates="asistencias")
    
    def __repr__(self):
        return f"<Asistencia alumno={self.alumno_id} fecha={self.fecha} estado={self.estado}>"
