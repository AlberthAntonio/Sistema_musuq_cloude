"""
Modelo de Matrícula.
Vincula un alumno a un periodo académico con sus datos académicos específicos.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Matricula(Base):
    """Modelo de matrícula - vincula alumno con periodo académico."""
    
    __tablename__ = "matriculas"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Código de matrícula único generado (ej: 26POA0001)
    codigo_matricula = Column(String(20), unique=True, nullable=False, index=True)
    
    # Relaciones FK
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), nullable=False, index=True)
    periodo_id = Column(Integer, ForeignKey("periodos_academicos.id"), nullable=False, index=True)
    
    # Datos académicos (trasladados desde Alumno)
    grupo = Column(String(10), nullable=True)       # A, B, C, D
    carrera = Column(String(100), nullable=True)     # Medicina, Ing...
    modalidad = Column(String(50), nullable=True)    # Ordinario, Primera Opción...
    horario = Column(String(50), nullable=True)      # MATUTINO, VESPERTINO, DOBLE HORARIO
    nivel = Column(String(20), nullable=True)        # PRIMARIA o SECUNDARIA (colegio)
    grado = Column(String(20), nullable=True)        # 1°, 2°, etc. (colegio)
    
    # Estado de la matrícula
    estado = Column(String(20), nullable=False, default="activo")  # 'activo', 'retirado'
    
    # Auditoría
    creado_por = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    
    # Timestamps
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones ORM
    alumno = relationship("Alumno", back_populates="matriculas")
    periodo = relationship("PeriodoAcademico", back_populates="matriculas")
    obligaciones = relationship("ObligacionPago", back_populates="matricula", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Matricula {self.codigo_matricula} alumno={self.alumno_id} periodo={self.periodo_id}>"
