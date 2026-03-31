"""
Modelo de Horario.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Horario(Base):
    """Modelo de horario de clases."""
    
    __tablename__ = "horarios"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relaciones
    curso_id = Column(Integer, ForeignKey("cursos.id"), nullable=False)
    docente_id = Column(Integer, ForeignKey("docentes.id"), nullable=True)
    plantilla_bloque_id = Column(
        Integer,
        ForeignKey("plantilla_bloques.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Grupo y periodo
    grupo = Column(String(10), nullable=False)  # A, B, C, D
    periodo = Column(String(20), default="2026-I")
    
    # Horario
    dia_semana = Column(Integer, nullable=False)  # 1=Lunes...6=Sábado
    hora_inicio = Column(String(5), nullable=False)  # "08:00"
    hora_fin = Column(String(5), nullable=False)     # "09:30"
    
    # Ubicación
    aula_id = Column(Integer, ForeignKey("aulas.id", ondelete="SET NULL"), nullable=True, index=True)
    aula = Column(String(50), nullable=True)  # Nombre display — sincronizado con aulas.nombre
    turno = Column(String(20), nullable=True)  # TURNO del bloque de clase: MAÑANA o TARDE
    # NOTA: No confundir con Alumno.horario (MATUTINO/VESPERTINO/DOBLE HORARIO)
    
    # Estado
    activo = Column(Boolean, default=True)
    
    # Timestamps
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    curso = relationship("Curso", back_populates="horarios")
    docente = relationship("Docente", back_populates="horarios")
    aula_obj = relationship("Aula", back_populates="horarios", foreign_keys=[aula_id])
    plantilla_bloque = relationship("PlantillaBloque", back_populates="horarios")
    
    @property
    def dia_nombre(self) -> str:
        dias = {1: 'LUNES', 2: 'MARTES', 3: 'MIÉRCOLES', 
                4: 'JUEVES', 5: 'VIERNES', 6: 'SÁBADO'}
        return dias.get(self.dia_semana, '')
    
    def __repr__(self):
        curso_nombre = self.curso.nombre if self.curso else 'Sin curso'
        return f"<Horario {curso_nombre} - {self.dia_nombre} {self.hora_inicio}>"
