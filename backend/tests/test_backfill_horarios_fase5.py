"""
Pruebas de Fase 5: backfill de horarios legacy a plantillas.
"""
import uuid
from typing import Optional

from app.models.aula import Aula
from app.models.curso import Curso
from app.models.horario import Horario
from app.services.backfill_horarios_service import backfill_horarios_to_plantillas


def _crear_aula(db_session, suffix: str) -> Aula:
    aula = Aula(nombre=f"AULA_F5_{suffix}", modalidad="COLEGIO", activo=True)
    db_session.add(aula)
    db_session.commit()
    db_session.refresh(aula)
    return aula


def _crear_curso(db_session, suffix: str) -> Curso:
    curso = Curso(nombre=f"CURSO_F5_{suffix}")
    db_session.add(curso)
    db_session.commit()
    db_session.refresh(curso)
    return curso


def _crear_horario_legacy(
    db_session,
    *,
    curso_id: int,
    aula_id: Optional[int],
    aula_nombre: Optional[str],
    grupo: str,
    periodo: str,
    turno: str,
    dia_semana: int,
    hora_inicio: str,
    hora_fin: str,
) -> Horario:
    horario = Horario(
        curso_id=curso_id,
        docente_id=None,
        grupo=grupo,
        periodo=periodo,
        dia_semana=dia_semana,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        aula_id=aula_id,
        aula=aula_nombre,
        turno=turno,
        plantilla_bloque_id=None,
        activo=True,
    )
    db_session.add(horario)
    db_session.commit()
    db_session.refresh(horario)
    return horario


def test_backfill_crea_plantilla_y_bloques_y_mapea(db_session):
    suffix = uuid.uuid4().hex[:8]
    grupo = f"G5_{suffix[:4]}"
    periodo = f"2026-{suffix[:2]}"
    aula = _crear_aula(db_session, suffix)
    curso = _crear_curso(db_session, suffix)

    h1 = _crear_horario_legacy(
        db_session,
        curso_id=curso.id,
        aula_id=aula.id,
        aula_nombre=aula.nombre,
        grupo=grupo,
        periodo=periodo,
        turno="MAÑANA",
        dia_semana=1,
        hora_inicio="08:00",
        hora_fin="08:45",
    )
    h2 = _crear_horario_legacy(
        db_session,
        curso_id=curso.id,
        aula_id=aula.id,
        aula_nombre=aula.nombre,
        grupo=grupo,
        periodo=periodo,
        turno="MANANA",
        dia_semana=1,
        hora_inicio="08:45",
        hora_fin="09:30",
    )

    report = backfill_horarios_to_plantillas(db_session, dry_run=False)

    assert report["plantillas_creadas"] >= 1
    assert report["bloques_creados"] >= 2
    assert report["horarios_mapeados"] >= 2

    db_session.refresh(h1)
    db_session.refresh(h2)
    assert h1.plantilla_bloque_id is not None
    assert h2.plantilla_bloque_id is not None


def test_backfill_es_idempotente(db_session):
    report_first = backfill_horarios_to_plantillas(db_session, dry_run=False)
    report_second = backfill_horarios_to_plantillas(db_session, dry_run=False)

    assert report_second["plantillas_creadas"] == 0
    assert report_second["bloques_creados"] == 0
    assert report_second["horarios_mapeados"] == 0
    assert report_second["horarios_ya_mapeados"] >= report_first["horarios_ya_mapeados"]


def test_backfill_reporta_no_mapeado_si_aula_no_resuelve(db_session):
    suffix = uuid.uuid4().hex[:8]
    grupo = f"G5_{suffix[:4]}"
    periodo = f"2026-{suffix[:2]}"
    curso = _crear_curso(db_session, suffix)

    horario = _crear_horario_legacy(
        db_session,
        curso_id=curso.id,
        aula_id=None,
        aula_nombre=f"AULA_F5_INEXISTENTE_{suffix}",
        grupo=grupo,
        periodo=periodo,
        turno="TARDE",
        dia_semana=2,
        hora_inicio="14:00",
        hora_fin="14:45",
    )

    report = backfill_horarios_to_plantillas(db_session, dry_run=False)

    assert report["horarios_no_mapeados"] >= 1
    assert any(
        item.get("horario_id") == horario.id and item.get("reason") == "aula_no_resuelta"
        for item in report["no_mapeados"]
    )
