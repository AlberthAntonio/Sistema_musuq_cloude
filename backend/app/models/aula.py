"""
Modelo de Aula y asignaciones académicas.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Aula(Base):
    """Modelo de aula física o lógica."""

    __tablename__ = "aulas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(80), unique=True, nullable=False)
    modalidad = Column(String(30), nullable=False, default="COLEGIO")
    descripcion = Column(String(255), nullable=True)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    grupos_asignados = relationship(
        "AulaGrupo",
        back_populates="aula",
        cascade="all, delete-orphan"
    )
    cursos_asignados = relationship(
        "AulaCurso",
        back_populates="aula",
        cascade="all, delete-orphan"
    )
    horarios = relationship(
        "Horario",
        back_populates="aula_obj",
        foreign_keys="[Horario.aula_id]",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<Aula {self.nombre} ({self.modalidad})>"


class AulaGrupo(Base):
    """Relación grupos habilitados para un aula."""

    __tablename__ = "aula_grupos"

    id = Column(Integer, primary_key=True, index=True)
    aula_id = Column(Integer, ForeignKey("aulas.id", ondelete="CASCADE"), nullable=False)
    grupo = Column(String(10), nullable=False)

    aula = relationship("Aula", back_populates="grupos_asignados")

    __table_args__ = (
        UniqueConstraint("aula_id", "grupo", name="_aula_grupo_uc"),
    )


class AulaCurso(Base):
    """Relación cursos permitidos en un aula."""

    __tablename__ = "aula_cursos"

    id = Column(Integer, primary_key=True, index=True)
    aula_id = Column(Integer, ForeignKey("aulas.id", ondelete="CASCADE"), nullable=False)
    curso_id = Column(Integer, ForeignKey("cursos.id"), nullable=False)

    aula = relationship("Aula", back_populates="cursos_asignados")
    curso = relationship("Curso")

    __table_args__ = (
        UniqueConstraint("aula_id", "curso_id", name="_aula_curso_uc"),
    )
