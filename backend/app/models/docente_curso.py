"""Modelo de relación muchos-a-muchos entre Docente y Curso."""

from sqlalchemy import Column, Integer, Boolean, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class DocenteCurso(Base):
	"""Asociación Docente-Curso."""

	__tablename__ = "docente_curso"

	id = Column(Integer, primary_key=True, index=True)
	docente_id = Column(Integer, ForeignKey("docentes.id", ondelete="CASCADE"), nullable=False, index=True)
	curso_id = Column(Integer, ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False, index=True)

	activo = Column(Boolean, default=True)
	fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

	docente = relationship("Docente", back_populates="docente_cursos")
	curso = relationship("Curso", back_populates="curso_docentes")

	__table_args__ = (
		UniqueConstraint("docente_id", "curso_id", name="uq_docente_curso"),
	)

	def __repr__(self) -> str:
		return f"<DocenteCurso docente_id={self.docente_id} curso_id={self.curso_id}>"