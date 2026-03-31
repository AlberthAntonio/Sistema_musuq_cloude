"""
Monitor operativo de rollout Fase 7 para horarios.

Consulta /metrics/summary y valida p95/error_rate en endpoints de horarios/plantillas.
Tambien reporta modo de rollout observado en /aulas/{id}/horarios usando headers.

Uso:
    python -m scripts.monitor_horarios_rollout_fase7

Variables opcionales:
    ROLLOUT_BASE_URL=http://127.0.0.1:8000
    ROLLOUT_USER=admin
    ROLLOUT_PASS=admin123
    ROLLOUT_AULA_IDS=1,2
    ROLLOUT_GRUPO=A
    ROLLOUT_PERIODO=2026-I
    ROLLOUT_TURNO=MANANA
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import httpx

BASE_URL = os.environ.get("ROLLOUT_BASE_URL", "http://127.0.0.1:8000")
USERNAME = os.environ.get("ROLLOUT_USER", "admin")
PASSWORD = os.environ.get("ROLLOUT_PASS", "admin123")
AULA_IDS = [x.strip() for x in os.environ.get("ROLLOUT_AULA_IDS", "").split(",") if x.strip()]
GRUPO = os.environ.get("ROLLOUT_GRUPO", "A")
PERIODO = os.environ.get("ROLLOUT_PERIODO", "2026-I")
TURNO = os.environ.get("ROLLOUT_TURNO", "MANANA")

P95_UMBRAL_MS = float(os.environ.get("ROLLOUT_P95_THRESHOLD_MS", "450"))
ERROR_RATE_UMBRAL = float(os.environ.get("ROLLOUT_ERROR_RATE_THRESHOLD", "1.0"))


def _login(client: httpx.Client) -> Dict[str, str]:
    res = client.post(
        f"{BASE_URL}/auth/login",
        data={"username": USERNAME, "password": PASSWORD},
        timeout=20.0,
    )
    res.raise_for_status()
    token = res.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


def _filter_horarios_endpoints(metrics: Dict[str, Any]) -> Dict[str, Any]:
    endpoints = metrics.get("endpoints", {})
    selected: Dict[str, Any] = {}
    for key, value in endpoints.items():
        if "/plantillas-horario" in key or "/aulas/{id}/horarios" in key or key.startswith("GET /horarios"):
            selected[key] = value
    return selected


def _sample_rollout_headers(client: httpx.Client, headers: Dict[str, str]) -> List[Dict[str, Any]]:
    if not AULA_IDS:
        return []

    samples: List[Dict[str, Any]] = []
    for aula_id in AULA_IDS:
        url = (
            f"{BASE_URL}/aulas/{aula_id}/horarios"
            f"?grupo={GRUPO}&periodo={PERIODO}&turno={TURNO}"
        )
        try:
            res = client.get(url, headers=headers, timeout=20.0)
            samples.append(
                {
                    "aula_id": aula_id,
                    "status_code": res.status_code,
                    "x_horarios_mode": res.headers.get("X-Horarios-Mode"),
                    "x_horarios_rollout_reason": res.headers.get("X-Horarios-Rollout-Reason"),
                }
            )
        except Exception as exc:
            samples.append(
                {
                    "aula_id": aula_id,
                    "status_code": None,
                    "error": str(exc),
                }
            )
    return samples


def run() -> Dict[str, Any]:
    with httpx.Client() as client:
        auth_headers = _login(client)

        res_metrics = client.get(f"{BASE_URL}/metrics/summary", headers=auth_headers, timeout=20.0)
        res_metrics.raise_for_status()
        metrics_data = res_metrics.json()

        horarios_endpoints = _filter_horarios_endpoints(metrics_data)

        violations: List[Dict[str, Any]] = []
        for endpoint, data in horarios_endpoints.items():
            p95 = float(data.get("latency_p95_ms") or 0)
            status_codes = data.get("status_codes") or {}
            request_count = max(float(data.get("request_count") or 0), 1.0)
            errors = 0.0
            for code, qty in status_codes.items():
                try:
                    code_int = int(code)
                except Exception:
                    continue
                if code_int >= 500:
                    errors += float(qty)
            error_rate = (errors / request_count) * 100.0

            if p95 > P95_UMBRAL_MS or error_rate > ERROR_RATE_UMBRAL:
                violations.append(
                    {
                        "endpoint": endpoint,
                        "latency_p95_ms": p95,
                        "error_rate_pct": round(error_rate, 3),
                        "threshold_p95_ms": P95_UMBRAL_MS,
                        "threshold_error_rate_pct": ERROR_RATE_UMBRAL,
                    }
                )

        rollout_samples = _sample_rollout_headers(client, auth_headers)

    report = {
        "report_type": "fase7_rollout_horarios_monitor",
        "timestamp": datetime.now().isoformat(),
        "base_url": BASE_URL,
        "thresholds": {
            "p95_ms": P95_UMBRAL_MS,
            "error_rate_pct": ERROR_RATE_UMBRAL,
        },
        "horarios_endpoints": horarios_endpoints,
        "rollout_header_samples": rollout_samples,
        "verdict": "OK" if not violations else "ALERTA",
        "violations": violations,
    }

    out_dir = Path(__file__).resolve().parent.parent / "benchmark_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"monitor_horarios_rollout_fase7_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=== MONITOR ROLLOUT FASE 7 HORARIOS ===")
    print(f"verdict: {report['verdict']}")
    print(f"violations: {len(violations)}")
    print(f"reporte_json: {out_path}")

    return report


if __name__ == "__main__":
    run()
