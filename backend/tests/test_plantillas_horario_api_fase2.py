"""
Pruebas de API para Fase 2 de plantillas de horario.
"""
import uuid

from app.models.aula import Aula


def _crear_aula(db_session) -> Aula:
    aula = Aula(nombre=f"AULA_F2_{uuid.uuid4().hex[:8]}", modalidad="COLEGIO", activo=True)
    db_session.add(aula)
    db_session.commit()
    db_session.refresh(aula)
    return aula


def test_crud_plantilla_y_bloques_happy_path(client, auth_headers, db_session):
    aula = _crear_aula(db_session)

    payload_plantilla = {
        "aula_id": aula.id,
        "grupo": "A",
        "periodo": "2026-I",
        "turno": "MANANA",
        "version": 1,
        "activo": True,
    }
    res_create = client.post("/plantillas-horario/", json=payload_plantilla, headers=auth_headers)
    assert res_create.status_code == 201
    plantilla = res_create.json()
    plantilla_id = plantilla["id"]

    payload_bloque = {
        "dia_semana": 1,
        "hora_inicio": "08:00",
        "hora_fin": "08:45",
        "tipo_bloque": "CLASE",
        "etiqueta": "Matematica",
        "orden_visual": 1,
        "activo": True,
    }
    res_bloque = client.post(
        f"/plantillas-horario/{plantilla_id}/bloques",
        json=payload_bloque,
        headers=auth_headers,
    )
    assert res_bloque.status_code == 201
    bloque = res_bloque.json()
    bloque_id = bloque["id"]

    res_list_bloques = client.get(f"/plantillas-horario/{plantilla_id}/bloques", headers=auth_headers)
    assert res_list_bloques.status_code == 200
    assert len(res_list_bloques.json()) == 1

    res_update = client.put(
        f"/plantilla-bloques/{bloque_id}",
        json={"etiqueta": "Matematica II"},
        headers=auth_headers,
    )
    assert res_update.status_code == 200
    assert res_update.json()["etiqueta"] == "Matematica II"

    res_batch = client.post(
        f"/plantillas-horario/{plantilla_id}/bloques/batch-upsert",
        json={
            "bloques": [
                {
                    "id": bloque_id,
                    "dia_semana": 1,
                    "hora_inicio": "08:00",
                    "hora_fin": "08:45",
                    "tipo_bloque": "CLASE",
                    "etiqueta": "Matematica III",
                    "orden_visual": 1,
                    "activo": True,
                },
                {
                    "dia_semana": 1,
                    "hora_inicio": "08:45",
                    "hora_fin": "09:30",
                    "tipo_bloque": "RECREO",
                    "etiqueta": "Descanso",
                    "orden_visual": 2,
                    "activo": True,
                },
            ],
            "eliminar_no_incluidos": False,
        },
        headers=auth_headers,
    )
    assert res_batch.status_code == 200
    body_batch = res_batch.json()
    assert body_batch["actualizados"] == 1
    assert body_batch["creados"] == 1

    res_grilla = client.get(
        f"/plantillas-horario/grilla-final?aula_id={aula.id}&grupo=A&periodo=2026-I&turno=MANANA",
        headers=auth_headers,
    )
    assert res_grilla.status_code == 200
    grilla = res_grilla.json()
    assert grilla["plantilla_id"] == plantilla_id
    assert "1" in grilla["bloques_por_dia"]
    assert len(grilla["bloques_por_dia"]["1"]) == 2

    res_delete_bloque = client.delete(f"/plantilla-bloques/{bloque_id}", headers=auth_headers)
    assert res_delete_bloque.status_code == 204

    res_delete_plantilla = client.delete(f"/plantillas-horario/{plantilla_id}", headers=auth_headers)
    assert res_delete_plantilla.status_code == 204


def test_conflicto_solape_devuelve_400(client, auth_headers, db_session):
    aula = _crear_aula(db_session)

    res_create = client.post(
        "/plantillas-horario/",
        json={
            "aula_id": aula.id,
            "grupo": "B",
            "periodo": "2026-I",
            "turno": "MANANA",
            "version": 1,
            "activo": True,
        },
        headers=auth_headers,
    )
    assert res_create.status_code == 201
    plantilla_id = res_create.json()["id"]

    ok_bloque = client.post(
        f"/plantillas-horario/{plantilla_id}/bloques",
        json={
            "dia_semana": 2,
            "hora_inicio": "10:00",
            "hora_fin": "10:45",
            "tipo_bloque": "CLASE",
            "activo": True,
        },
        headers=auth_headers,
    )
    assert ok_bloque.status_code == 201

    conflicto = client.post(
        f"/plantillas-horario/{plantilla_id}/bloques",
        json={
            "dia_semana": 2,
            "hora_inicio": "10:30",
            "hora_fin": "11:15",
            "tipo_bloque": "CLASE",
            "activo": True,
        },
        headers=auth_headers,
    )
    assert conflicto.status_code == 400
    assert "superpuesto" in conflicto.json()["detail"].lower()


def test_tipo_bloque_invalido_devuelve_422(client, auth_headers, db_session):
    aula = _crear_aula(db_session)

    res_create = client.post(
        "/plantillas-horario/",
        json={
            "aula_id": aula.id,
            "grupo": "C",
            "periodo": "2026-I",
            "turno": "TARDE",
            "version": 1,
            "activo": True,
        },
        headers=auth_headers,
    )
    assert res_create.status_code == 201
    plantilla_id = res_create.json()["id"]

    invalido = client.post(
        f"/plantillas-horario/{plantilla_id}/bloques",
        json={
            "dia_semana": 3,
            "hora_inicio": "14:00",
            "hora_fin": "14:45",
            "tipo_bloque": "OTRO",
            "activo": True,
        },
        headers=auth_headers,
    )
    assert invalido.status_code == 422
