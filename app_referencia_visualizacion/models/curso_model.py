from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class Curso(Base):
    __tablename__ = "cursos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    
    # Relación inversa
    asignaciones = relationship("MallaCurricular", back_populates="curso", cascade="all, delete-orphan")

    def __repr__(self):
        return self.nombre

class MallaCurricular(Base):
    __tablename__ = "malla_curricular"
    id = Column(Integer, primary_key=True, index=True)
    grupo = Column(String, nullable=False) # A, B, C, D...
    curso_id = Column(Integer, ForeignKey("cursos.id"), nullable=False)

    curso = relationship("Curso", back_populates="asignaciones")

    # Regla: No puedes asignar el mismo curso dos veces al mismo grupo
    __table_args__ = (UniqueConstraint('grupo', 'curso_id', name='_grupo_curso_uc'),)