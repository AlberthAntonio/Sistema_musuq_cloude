"""
Benchmark de Fase 6 para endpoints nuevos de horarios/plantillas.
Mide latencia p50/p95 y registra presencia de errores 5xx.

Ejecucion:
    python -m scripts.benchmark_horarios_fase6
"""
from __future__ import annotations

import json
import os
import statistics
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import SessionLocal
from app.models.aula import Aula
from app.models.usuario import Usuario
from app.services.plantilla_horario_service import plantilla_horario_service
from main import app

ITERATIONS = int(os.environ.get("HORARIOS_BENCHMARK_ITERATIONS", "25"))


def _percentile(data: List[float], p: float) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return round(sorted_data[f], 2)
    return round(sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f]), 2)


def _auth_headers(client: TestClient) -> Dict[str, str]:
    username = os.environ.get("BENCHMARK_USER", "test_admin")
    password = os.environ.get("BENCHMARK_PASS", "testpass123")

    res = client.post("/auth/login", data={"username": username, "password": password})
    if res.status_code != 200:
        raise RuntimeError(f"No se pudo autenticar benchmark: {res.status_code} {res.text}")

    token = res.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


def _ensure_benchmark_user() -> None:
    username = os.environ.get("BENCHMARK_USER", "test_admin")
    password = os.environ.get("BENCHMARK_PASS", "testpass123")

    db = SessionLocal()
    try:
        user = db.query(Usuario).filter(Usuario.username == username).first()
        hashed = get_password_hash(password)
        if user is None:
            user = Usuario(
                username=username,
                email=f"{username}@benchmark.local",
                nombre_completo="Benchmark Admin",
                rol="admin",
                hashed_password=hashed,
                activo=True,
            )
            db.add(user)
        else:
            user.hashed_password = hashed
            user.rol = "admin"
            user.activo = True
        db.commit()
    finally:
        db.close()


def _seed_fixture() -> Dict[str, Any]:
    db = SessionLocal()
    try:
        suffix = uuid.uuid4().hex[:8]
        grupo = f"G6_{suffix[:4]}"
        periodo = "2026-I"
        turno = "MANANA"

        aula = Aula(nombre=f"AULA_BENCH_F6_{suffix}", modalidad="COLEGIO", activo=True)
        db.add(aula)
        db.commit()
        db.refresh(aula)

        plantilla = plantilla_horario_service.crear_plantilla(
            db,
            aula_id=aula.id,
            grupo=grupo,
            periodo=periodo,
            turno=turno,
        )

        bloque = plantilla_horario_service.crear_bloque(
            db,
            plantilla_id=plantilla.id,
            dia_semana=1,
            hora_inicio="08:00",
            hora_fin="08:45",
            tipo_bloque="CLASE",
            etiqueta="Benchmark",
            orden_visual=1,
        )

        return {
            "aula_id": aula.id,
            "grupo": grupo,
            "periodo": periodo,
            "turno": turno,
            "plantilla_id": plantilla.id,
            "bloque_id": bloque.id,
        }
    finally:
        db.close()


def _measure_endpoint(client: TestClient, method: str, path: str, headers: Dict[str, str], json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    latencies: List[float] = []
    status_codes: List[int] = []
    five_xx = 0

    for _ in range(ITERATIONS):
        t0 = time.perf_counter()
        if method == "GET":
            res = client.get(path, headers=headers)
        elif method == "POST":
            res = client.post(path, headers=headers, json=json_body or {})
        else:
            raise ValueError(f"Metodo no soportado: {method}")
        elapsed_ms = (time.perf_counter() - t0) * 1000

        latencies.append(elapsed_ms)
        status_codes.append(res.status_code)
        if res.status_code >= 500:
            five_xx += 1

    return {
        "iterations": ITERATIONS,
        "status_codes_sample": status_codes[:5],
        "errors_5xx": five_xx,
        "latency_p50_ms": _percentile(latencies, 50),
        "latency_p95_ms": _percentile(latencies, 95),
        "latency_p99_ms": _percentile(latencies, 99),
        "latency_avg_ms": round(statistics.mean(latencies), 2),
        "latency_min_ms": round(min(latencies), 2),
        "latency_max_ms": round(max(latencies), 2),
    }


def run() -> Dict[str, Any]:
    _ensure_benchmark_user()
    fixture = _seed_fixture()

    with TestClient(app) as client:
        headers = _auth_headers(client)

        endpoints = {
            "GET /plantillas-horario/": _measure_endpoint(
                client,
                "GET",
                "/plantillas-horario/?activo=true",
                headers,
            ),
            "GET /plantillas-horario/{id}/bloques": _measure_endpoint(
                client,
                "GET",
                f"/plantillas-horario/{fixture['plantilla_id']}/bloques?activo=true",
                headers,
            ),
            "GET /plantillas-horario/grilla-final": _measure_endpoint(
                client,
                "GET",
                (
                    "/plantillas-horario/grilla-final"
                    f"?aula_id={fixture['aula_id']}"
                    f"&grupo={fixture['grupo']}"
                    f"&periodo={fixture['periodo']}"
                    f"&turno={fixture['turno']}"
                ),
                headers,
            ),
            "POST /plantillas-horario/{id}/bloques/batch-upsert": _measure_endpoint(
                client,
                "POST",
                f"/plantillas-horario/{fixture['plantilla_id']}/bloques/batch-upsert",
                headers,
                json_body={
                    "bloques": [
                        {
                            "id": fixture["bloque_id"],
                            "dia_semana": 1,
                            "hora_inicio": "08:00",
                            "hora_fin": "08:45",
                            "tipo_bloque": "CLASE",
                            "etiqueta": "Benchmark update",
                            "orden_visual": 1,
                            "activo": True,
                        }
                    ],
                    "eliminar_no_incluidos": False,
                },
            ),
        }

    all_5xx = sum(v["errors_5xx"] for v in endpoints.values())
    max_p95 = max(v["latency_p95_ms"] for v in endpoints.values()) if endpoints else 0.0

    report = {
        "benchmark_type": "fase6_horarios_endpoints",
        "timestamp": datetime.now().isoformat(),
        "iterations": ITERATIONS,
        "fixture": fixture,
        "results": endpoints,
        "verifications": {
            "sin_errores_5xx": all_5xx == 0,
            "errores_5xx_totales": all_5xx,
            "p95_max_ms": max_p95,
        },
    }

    output_dir = Path(__file__).resolve().parent.parent / "benchmark_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"benchmark_horarios_fase6_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=== BENCHMARK FASE 6 HORARIOS ===")
    for endpoint, data in endpoints.items():
        print(
            f"{endpoint} | p50={data['latency_p50_ms']}ms "
            f"p95={data['latency_p95_ms']}ms 5xx={data['errors_5xx']}"
        )
    print(f"reporte_json: {output_path}")

    return report


if __name__ == "__main__":
    run()
