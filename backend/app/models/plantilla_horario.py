"""
Modelos de plantillas de horario (fase 1).
"""
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class PlantillaHorario(Base):
    """Plantilla de jornada por aula, grupo, periodo y turno."""

    __tablename__ = "plantillas_horario"

    id = Column(Integer, primary_key=True, index=True)
    aula_id = Column(Integer, ForeignKey("aulas.id", ondelete="CASCADE"), nullable=False)
    grupo = Column(String(10), nullable=False)
    periodo = Column(String(20), nullable=False)
    turno = Column(String(20), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    aula = relationship("Aula")
    bloques = relationship(
        "PlantillaBloque",
        back_populates="plantilla",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index(
            "ix_plantillas_horario_aula_grupo_periodo_turno_activo",
            "aula_id",
            "grupo",
            "periodo",
            "turno",
            "activo",
        ),
    )


class PlantillaBloque(Base):
    """Bloques de tiempo configurables por dia para una plantilla."""

    __tablename__ = "plantilla_bloques"

    id = Column(Integer, primary_key=True, index=True)
    plantilla_id = Column(
        Integer,
        ForeignKey("plantillas_horario.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dia_semana = Column(Integer, nullable=False)
    hora_inicio = Column(String(5), nullable=False)
    hora_fin = Column(String(5), nullable=False)
    tipo_bloque = Column(String(20), nullable=False)
    etiqueta = Column(String(100), nullable=True)
    orden_visual = Column(Integer, nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    plantilla = relationship("PlantillaHorario", back_populates="bloques")
    horarios = relationship("Horario", back_populates="plantilla_bloque")

    __table_args__ = (
        CheckConstraint("dia_semana >= 1 AND dia_semana <= 6", name="ck_plantilla_bloques_dia_semana"),
        CheckConstraint("hora_inicio < hora_fin", name="ck_plantilla_bloques_horas"),
        CheckConstraint(
            "tipo_bloque IN ('CLASE', 'RECREO', 'LIBRE')",
            name="ck_plantilla_bloques_tipo",
        ),
        Index(
            "ix_plantilla_bloques_plantilla_dia_inicio",
            "plantilla_id",
            "dia_semana",
            "hora_inicio",
        ),
    )
