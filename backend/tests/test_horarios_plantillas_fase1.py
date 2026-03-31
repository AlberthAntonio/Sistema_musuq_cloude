"""
Pruebas base de Fase 1 para plantillas de horario.
"""
import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.aula import Aula
from app.models.curso import Curso
from app.models.horario import Horario
from app.models.plantilla_horario import PlantillaBloque
from app.services.plantilla_horario_service import plantilla_horario_service


def _crear_aula(db_session, suffix: str) -> Aula:
    aula = Aula(nombre=f"AULA_FASE1_{suffix}", modalidad="COLEGIO", activo=True)
    db_session.add(aula)
    db_session.commit()
    db_session.refresh(aula)
    return aula


def _crear_curso(db_session, suffix: str) -> Curso:
    curso = Curso(nombre=f"CURSO_FASE1_{suffix}")
    db_session.add(curso)
    db_session.commit()
    db_session.refresh(curso)
    return curso


def test_crear_bloque_valido_servicio(db_session):
    suffix = uuid.uuid4().hex[:8]
    aula = _crear_aula(db_session, suffix)

    plantilla = plantilla_horario_service.crear_plantilla(
        db_session,
        aula_id=aula.id,
        grupo="A",
        periodo="2026-I",
        turno="MANANA",
    )

    bloque = plantilla_horario_service.crear_bloque(
        db_session,
        plantilla_id=plantilla.id,
        dia_semana=1,
        hora_inicio="08:00",
        hora_fin="08:45",
        tipo_bloque="CLASE",
        etiqueta="Matematica",
    )

    assert bloque.id is not None
    assert bloque.tipo_bloque == "CLASE"


def test_crear_bloque_horas_invalidas_falla_por_constraint(db_session):
    suffix = uuid.uuid4().hex[:8]
    aula = _crear_aula(db_session, suffix)

    plantilla = plantilla_horario_service.crear_plantilla(
        db_session,
        aula_id=aula.id,
        grupo="B",
        periodo="2026-I",
        turno="MANANA",
    )

    bloque_invalido = PlantillaBloque(
        plantilla_id=plantilla.id,
        dia_semana=1,
        hora_inicio="09:00",
        hora_fin="08:45",
        tipo_bloque="CLASE",
        activo=True,
    )
    db_session.add(bloque_invalido)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_horario_acepta_fk_plantilla_bloque(db_session):
    suffix = uuid.uuid4().hex[:8]
    aula = _crear_aula(db_session, suffix)
    curso = _crear_curso(db_session, suffix)

    plantilla = plantilla_horario_service.crear_plantilla(
        db_session,
        aula_id=aula.id,
        grupo="C",
        periodo="2026-I",
        turno="TARDE",
    )
    bloque = plantilla_horario_service.crear_bloque(
        db_session,
        plantilla_id=plantilla.id,
        dia_semana=2,
        hora_inicio="14:00",
        hora_fin="14:45",
        tipo_bloque="CLASE",
    )

    horario = Horario(
        curso_id=curso.id,
        docente_id=None,
        grupo="C",
        periodo="2026-I",
        dia_semana=2,
        hora_inicio="14:00",
        hora_fin="14:45",
        aula_id=aula.id,
        aula=aula.nombre,
        turno="TARDE",
        plantilla_bloque_id=bloque.id,
        activo=True,
    )
    db_session.add(horario)
    db_session.commit()
    db_session.refresh(horario)

    assert horario.id is not None
    assert horario.plantilla_bloque_id == bloque.id


def test_servicio_rechaza_solape(db_session):
    suffix = uuid.uuid4().hex[:8]
    aula = _crear_aula(db_session, suffix)

    plantilla = plantilla_horario_service.crear_plantilla(
        db_session,
        aula_id=aula.id,
        grupo="D",
        periodo="2026-I",
        turno="MANANA",
    )
    plantilla_horario_service.crear_bloque(
        db_session,
        plantilla_id=plantilla.id,
        dia_semana=3,
        hora_inicio="10:00",
        hora_fin="10:45",
        tipo_bloque="CLASE",
    )

    with pytest.raises(ValueError, match="superpuesto"):
        plantilla_horario_service.crear_bloque(
            db_session,
            plantilla_id=plantilla.id,
            dia_semana=3,
            hora_inicio="10:30",
            hora_fin="11:15",
            tipo_bloque="CLASE",
        )
