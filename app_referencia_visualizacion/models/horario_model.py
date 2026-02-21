# app/models/horario_model.py

from sqlalchemy import Column, Integer, String, Time, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Horario(Base):
    __tablename__ = "horarios"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relaciones
    curso_id = Column(Integer, ForeignKey("cursos.id"), nullable=False)
    docente_id = Column(Integer, ForeignKey("docentes.id"), nullable=True)
    
    # Grupo y periodo
    grupo = Column(String(10), nullable=False)
    periodo = Column(String(20), default="2026-I")
    
    # Horario
    dia_semana = Column(Integer, nullable=False)  # 1=Lunes...6=Sábado
    hora_inicio = Column(String(5), nullable=False)  # "08:00"
    hora_fin = Column(String(5), nullable=False)     # "09:30"
    
    # Ubicación
    aula = Column(String(50), nullable=True)
    turno = Column(String(20), nullable=True)  # MAÑANA, TARDE
    
    # Metadata
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now)
    
    # Relaciones
    curso = relationship("Curso", backref="horarios")
    docente = relationship("Docente", back_populates="horarios")
    
    @property
    def dia_nombre(self):
        dias = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 
                4: 'Jueves', 5: 'Viernes', 6: 'Sábado'}
        return dias.get(self.dia_semana, '')
    
    def __repr__(self):
        return f"<Horario {self.curso.nombre if self.curso else 'Sin curso'} - {self.dia_nombre} {self.hora_inicio}>"
