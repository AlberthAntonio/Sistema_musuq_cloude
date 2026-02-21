# app/models/evento_model.py

from sqlalchemy import Column, Integer, String, Date, Time, Boolean, DateTime, Text
from datetime import datetime
from app.database import Base

class EventoCalendario(Base):
    __tablename__ = "eventos_calendario"
    
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    
    # Fecha y hora
    fecha = Column(Date, nullable=False)
    hora_inicio = Column(String(5), nullable=True)  # "08:00"
    hora_fin = Column(String(5), nullable=True)     # "10:00"
    
    # Clasificación
    tipo = Column(String(50), nullable=True)  # examen, reunion, feriado, evento
    grupo = Column(String(10), nullable=True)  # A, B, C, null=todos
    
    # Visibilidad
    publico = Column(Boolean, default=True)  # True=todos ven, False=solo admin
    activo = Column(Boolean, default=True)
    
    fecha_creacion = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Evento {self.titulo} - {self.fecha}>"
