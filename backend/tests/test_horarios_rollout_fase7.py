"""
Pruebas de rollout Fase 7 para horarios dinamicos con feature flags.
"""
import uuid

from app.core.config import settings
from app.models.aula import Aula
from app.services.plantilla_horario_service import plantilla_horario_service


def _crear_aula(db_session) -> Aula:
    aula = Aula(nombre=f"AULA_F7_{uuid.uuid4().hex[:8]}", modalidad="COLEGIO", activo=True)
    db_session.add(aula)
    db_session.commit()
    db_session.refresh(aula)
    return aula


def test_rollout_flag_global_off_fuerza_legacy(client, auth_headers, db_session):
    aula = _crear_aula(db_session)

    plantilla = plantilla_horario_service.crear_plantilla(
        db_session,
        aula_id=aula.id,
        grupo="A",
        periodo="2026-I",
        turno="MANANA",
    )
    plantilla_horario_service.crear_bloque(
        db_session,
        plantilla_id=plantilla.id,
        dia_semana=1,
        hora_inicio="08:00",
        hora_fin="08:45",
        tipo_bloque="RECREO",
        etiqueta="Descanso",
        orden_visual=1,
    )

    prev_enabled = settings.HORARIOS_PLANTILLAS_ENABLED
    prev_allow = settings.HORARIOS_PLANTILLAS_ALLOW_AULAS
    try:
        settings.HORARIOS_PLANTILLAS_ENABLED = False
        settings.HORARIOS_PLANTILLAS_ALLOW_AULAS = "*"

        res = client.get(
            f"/aulas/{aula.id}/horarios?grupo=A&periodo=2026-I&turno=MANANA",
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert res.headers.get("X-Horarios-Mode") == "legacy"
        assert res.headers.get("X-Horarios-Rollout-Reason") == "feature_flag_disabled"
        assert res.json() == []
    finally:
        settings.HORARIOS_PLANTILLAS_ENABLED = prev_enabled
        settings.HORARIOS_PLANTILLAS_ALLOW_AULAS = prev_allow


def test_rollout_allowlist_controla_modo_dinamico(client, auth_headers, db_session):
    aula_allow = _crear_aula(db_session)
    aula_block = _crear_aula(db_session)

    for aula in (aula_allow, aula_block):
        plantilla = plantilla_horario_service.crear_plantilla(
            db_session,
            aula_id=aula.id,
            grupo="B",
            periodo="2026-I",
            turno="MANANA",
        )
        plantilla_horario_service.crear_bloque(
            db_session,
            plantilla_id=plantilla.id,
            dia_semana=1,
            hora_inicio="09:00",
            hora_fin="09:45",
            tipo_bloque="RECREO",
            etiqueta="Break",
            orden_visual=1,
        )

    prev_enabled = settings.HORARIOS_PLANTILLAS_ENABLED
    prev_allow = settings.HORARIOS_PLANTILLAS_ALLOW_AULAS
    try:
        settings.HORARIOS_PLANTILLAS_ENABLED = True
        settings.HORARIOS_PLANTILLAS_ALLOW_AULAS = str(aula_allow.id)

        res_allow = client.get(
            f"/aulas/{aula_allow.id}/horarios?grupo=B&periodo=2026-I&turno=MANANA",
            headers=auth_headers,
        )
        assert res_allow.status_code == 200
        assert res_allow.headers.get("X-Horarios-Mode") == "dynamic"
        assert res_allow.headers.get("X-Horarios-Rollout-Reason") == "enabled_allowlist_aula"
        assert any(item.get("tipo_bloque") == "RECREO" for item in res_allow.json())

        res_block = client.get(
            f"/aulas/{aula_block.id}/horarios?grupo=B&periodo=2026-I&turno=MANANA",
            headers=auth_headers,
        )
        assert res_block.status_code == 200
        assert res_block.headers.get("X-Horarios-Mode") == "legacy"
        assert res_block.headers.get("X-Horarios-Rollout-Reason") == "aula_outside_allowlist"
        assert res_block.json() == []
    finally:
        settings.HORARIOS_PLANTILLAS_ENABLED = prev_enabled
        settings.HORARIOS_PLANTILLAS_ALLOW_AULAS = prev_allow
