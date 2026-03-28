"""
Modelo de Curso y Malla Curricular.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Curso(Base):
    """Modelo de curso académico."""
    
    __tablename__ = "cursos"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(255), nullable=True)
    
    # Timestamps
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    asignaciones = relationship("MallaCurricular", back_populates="curso", cascade="all, delete-orphan")
    horarios = relationship("Horario", back_populates="curso", cascade="all, delete-orphan")

    # Relación con docentes (muchos-a-muchos) a través de DocenteCurso
    curso_docentes = relationship(
        "DocenteCurso",
        back_populates="curso",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return self.nombre


class MallaCurricular(Base):
    """Modelo de asignación de cursos a grupos."""
    
    __tablename__ = "malla_curricular"
    
    id = Column(Integer, primary_key=True, index=True)
    grupo = Column(String(10), nullable=False)  # A, B, C, D...
    curso_id = Column(Integer, ForeignKey("cursos.id"), nullable=False)
    
    # Relación
    curso = relationship("Curso", back_populates="asignaciones")
    
    # Restricción única: No se puede asignar el mismo curso dos veces al mismo grupo
    __table_args__ = (UniqueConstraint('grupo', 'curso_id', name='_grupo_curso_uc'),)
    
    def __repr__(self):
        return f"<Malla {self.grupo}: {self.curso.nombre if self.curso else 'Sin curso'}>"
