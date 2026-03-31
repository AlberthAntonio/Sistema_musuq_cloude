"""
Pruebas de calidad, rendimiento y observabilidad de Fase 6 para horarios.
"""
import time
import uuid

from app.models.aula import Aula


def _percentile(values, p):
    if not values:
        return 0.0
    data = sorted(values)
    k = (len(data) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(data):
        return data[f]
    return data[f] + (k - f) * (data[c] - data[f])


def _crear_aula(db_session) -> Aula:
    aula = Aula(nombre=f"AULA_F6_{uuid.uuid4().hex[:8]}", modalidad="COLEGIO", activo=True)
    db_session.add(aula)
    db_session.commit()
    db_session.refresh(aula)
    return aula


def test_fase6_request_id_en_headers_en_flujo_plantillas(client, auth_headers, db_session):
    aula = _crear_aula(db_session)
    grupo = f"G6_{uuid.uuid4().hex[:4]}"

    res_create = client.post(
        "/plantillas-horario/",
        json={
            "aula_id": aula.id,
            "grupo": grupo,
            "periodo": "2026-I",
            "turno": "MANANA",
            "version": 1,
            "activo": True,
        },
        headers=auth_headers,
    )
    assert res_create.status_code == 201
    assert res_create.headers.get("X-Request-ID")
    plantilla_id = res_create.json()["id"]

    res_list = client.get(
        f"/plantillas-horario/{plantilla_id}/bloques",
        headers=auth_headers,
    )
    assert res_list.status_code == 200
    assert res_list.headers.get("X-Request-ID")


def test_fase6_sin_5xx_en_flujo_principal_plantillas(client, auth_headers, db_session):
    aula = _crear_aula(db_session)
    grupo = f"G6_{uuid.uuid4().hex[:4]}"

    crear_plantilla = client.post(
        "/plantillas-horario/",
        json={
            "aula_id": aula.id,
            "grupo": grupo,
            "periodo": "2026-I",
            "turno": "MANANA",
            "version": 1,
            "activo": True,
        },
        headers=auth_headers,
    )
    assert crear_plantilla.status_code < 500
    plantilla_id = crear_plantilla.json()["id"]

    crear_bloque = client.post(
        f"/plantillas-horario/{plantilla_id}/bloques",
        json={
            "dia_semana": 1,
            "hora_inicio": "08:00",
            "hora_fin": "08:45",
            "tipo_bloque": "CLASE",
            "etiqueta": "Bloque QA",
            "orden_visual": 1,
            "activo": True,
        },
        headers=auth_headers,
    )
    assert crear_bloque.status_code < 500
    bloque_id = crear_bloque.json()["id"]

    actualizar_bloque = client.put(
        f"/plantilla-bloques/{bloque_id}",
        json={"etiqueta": "Bloque QA 2"},
        headers=auth_headers,
    )
    assert actualizar_bloque.status_code < 500

    grilla = client.get(
        f"/plantillas-horario/grilla-final?aula_id={aula.id}&grupo={grupo}&periodo=2026-I&turno=MANANA",
        headers=auth_headers,
    )
    assert grilla.status_code < 500

    eliminar_bloque = client.delete(f"/plantilla-bloques/{bloque_id}", headers=auth_headers)
    assert eliminar_bloque.status_code < 500

    eliminar_plantilla = client.delete(f"/plantillas-horario/{plantilla_id}", headers=auth_headers)
    assert eliminar_plantilla.status_code < 500


def test_fase6_p95_endpoints_nuevos_estable(client, auth_headers, db_session):
    aula = _crear_aula(db_session)
    grupo = f"G6_{uuid.uuid4().hex[:4]}"

    crear_plantilla = client.post(
        "/plantillas-horario/",
        json={
            "aula_id": aula.id,
            "grupo": grupo,
            "periodo": "2026-I",
            "turno": "MANANA",
            "version": 1,
            "activo": True,
        },
        headers=auth_headers,
    )
    assert crear_plantilla.status_code == 201
    plantilla_id = crear_plantilla.json()["id"]

    crear_bloque = client.post(
        f"/plantillas-horario/{plantilla_id}/bloques",
        json={
            "dia_semana": 2,
            "hora_inicio": "09:00",
            "hora_fin": "09:45",
            "tipo_bloque": "CLASE",
            "etiqueta": "Performance",
            "orden_visual": 1,
            "activo": True,
        },
        headers=auth_headers,
    )
    assert crear_bloque.status_code == 201

    lat_list = []
    lat_grilla = []

    for _ in range(20):
        t0 = time.perf_counter()
        r1 = client.get("/plantillas-horario/?activo=true", headers=auth_headers)
        lat_list.append((time.perf_counter() - t0) * 1000)
        assert r1.status_code == 200

        t1 = time.perf_counter()
        r2 = client.get(
            f"/plantillas-horario/grilla-final?aula_id={aula.id}&grupo={grupo}&periodo=2026-I&turno=MANANA",
            headers=auth_headers,
        )
        lat_grilla.append((time.perf_counter() - t1) * 1000)
        assert r2.status_code == 200

    p95_list = _percentile(lat_list, 95)
    p95_grilla = _percentile(lat_grilla, 95)

    # Umbral conservador para entorno de prueba local/CI.
    assert p95_list < 800
    assert p95_grilla < 800
