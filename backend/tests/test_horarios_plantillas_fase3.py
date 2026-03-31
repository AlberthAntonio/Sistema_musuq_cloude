"""
Pruebas de integracion de Fase 3: horarios + plantillas.
"""
import uuid

from app.models.aula import Aula
from app.models.curso import Curso
from app.services.plantilla_horario_service import plantilla_horario_service


def _crear_aula(db_session) -> Aula:
    aula = Aula(nombre=f"AULA_F3_{uuid.uuid4().hex[:8]}", modalidad="COLEGIO", activo=True)
    db_session.add(aula)
    db_session.commit()
    db_session.refresh(aula)
    return aula


def _crear_curso(db_session) -> Curso:
    curso = Curso(nombre=f"CURSO_F3_{uuid.uuid4().hex[:8]}")
    db_session.add(curso)
    db_session.commit()
    db_session.refresh(curso)
    return curso


def _crear_contexto_plantilla(db_session, aula_id: int, grupo: str = "A", turno: str = "MANANA"):
    plantilla = plantilla_horario_service.crear_plantilla(
        db_session,
        aula_id=aula_id,
        grupo=grupo,
        periodo="2026-I",
        turno=turno,
    )
    bloque_clase = plantilla_horario_service.crear_bloque(
        db_session,
        plantilla_id=plantilla.id,
        dia_semana=1,
        hora_inicio="08:00",
        hora_fin="08:45",
        tipo_bloque="CLASE",
        etiqueta="Bloque clase",
        orden_visual=1,
    )
    bloque_recreo = plantilla_horario_service.crear_bloque(
        db_session,
        plantilla_id=plantilla.id,
        dia_semana=1,
        hora_inicio="08:45",
        hora_fin="09:00",
        tipo_bloque="RECREO",
        etiqueta="Descanso",
        orden_visual=2,
    )
    return plantilla, bloque_clase, bloque_recreo


def test_crear_horario_con_plantilla_bloque_clase_valido(client, auth_headers, db_session):
    aula = _crear_aula(db_session)
    curso = _crear_curso(db_session)
    _, bloque_clase, _ = _crear_contexto_plantilla(db_session, aula.id)

    payload = {
        "curso_id": curso.id,
        "grupo": "A",
        "periodo": "2026-I",
        "dia_semana": 1,
        "hora_inicio": "08:00",
        "hora_fin": "08:45",
        "aula_id": aula.id,
        "turno": "MANANA",
        "plantilla_bloque_id": bloque_clase.id,
    }
    res = client.post("/horarios/", json=payload, headers=auth_headers)

    assert res.status_code == 201
    body = res.json()
    assert body["plantilla_bloque_id"] == bloque_clase.id
    assert body["dia_semana"] == 1
    assert body["hora_inicio"] == "08:00"
    assert body["hora_fin"] == "08:45"


def test_rechaza_asignacion_en_bloque_no_clase(client, auth_headers, db_session):
    aula = _crear_aula(db_session)
    curso = _crear_curso(db_session)
    _, _, bloque_recreo = _crear_contexto_plantilla(db_session, aula.id)

    payload = {
        "curso_id": curso.id,
        "grupo": "A",
        "periodo": "2026-I",
        "dia_semana": 1,
        "hora_inicio": "08:45",
        "hora_fin": "09:00",
        "aula_id": aula.id,
        "turno": "MANANA",
        "plantilla_bloque_id": bloque_recreo.id,
    }
    res = client.post("/horarios/", json=payload, headers=auth_headers)

    assert res.status_code == 400
    assert "CLASE" in res.json()["detail"]


def test_flujo_legacy_sigue_operativo_en_horarios_aula(client, auth_headers, db_session):
    aula = _crear_aula(db_session)
    curso = _crear_curso(db_session)

    crear = client.post(
        "/horarios/",
        json={
            "curso_id": curso.id,
            "grupo": "B",
            "periodo": "2026-I",
            "dia_semana": 2,
            "hora_inicio": "10:00",
            "hora_fin": "10:45",
            "aula_id": aula.id,
            "aula": aula.nombre,
            "turno": "MANANA",
        },
        headers=auth_headers,
    )
    assert crear.status_code == 201
    creado_id = crear.json()["id"]

    res_horarios = client.get(
        f"/aulas/{aula.id}/horarios?periodo=2026-I",
        headers=auth_headers,
    )
    assert res_horarios.status_code == 200

    items = res_horarios.json()
    assert any(h.get("id") == creado_id for h in items)


def test_horarios_aula_consume_estructura_dinamica_por_grupo(client, auth_headers, db_session):
    aula = _crear_aula(db_session)
    curso = _crear_curso(db_session)
    _, bloque_clase, _ = _crear_contexto_plantilla(db_session, aula.id, grupo="C", turno="TARDE")

    crear = client.post(
        "/horarios/",
        json={
            "curso_id": curso.id,
            "grupo": "C",
            "periodo": "2026-I",
            "dia_semana": 1,
            "hora_inicio": "08:00",
            "hora_fin": "08:45",
            "aula_id": aula.id,
            "turno": "TARDE",
            "plantilla_bloque_id": bloque_clase.id,
        },
        headers=auth_headers,
    )
    assert crear.status_code == 201
    horario_id = crear.json()["id"]

    res_horarios = client.get(
        f"/aulas/{aula.id}/horarios?periodo=2026-I&grupo=C",
        headers=auth_headers,
    )
    assert res_horarios.status_code == 200
    items = res_horarios.json()

    assert any(h.get("tipo_bloque") == "RECREO" for h in items)
    assert any(
        h.get("id") == horario_id
        and h.get("tipo_bloque") == "CLASE"
        and h.get("plantilla_bloque_id") == bloque_clase.id
        for h in items
    )
