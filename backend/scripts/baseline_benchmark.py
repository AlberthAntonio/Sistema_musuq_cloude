"""
Script de Benchmark Baseline.
Mide latencia (p50, p95, p99), tamaño de payload, y genera informe JSON.
Ejecutar: python scripts/baseline_benchmark.py

Requisitos:
  - El server debe estar corriendo en localhost:8000
  - Debe existir un usuario admin para obtener token
"""
import httpx
import json
import time
import statistics
import sys
import os
import concurrent.futures
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuración del benchmark
BASE_URL = os.environ.get("BENCHMARK_URL", "http://localhost:8000")
USERNAME = os.environ.get("BENCHMARK_USER", "admin")
PASSWORD = os.environ.get("BENCHMARK_PASS", "admin123")
ITERATIONS = int(os.environ.get("BENCHMARK_ITERATIONS", "10"))

# Endpoints críticos a medir (del Plan Maestro §3)
CRITICAL_ENDPOINTS = [
    {"method": "GET", "path": "/alumnos", "params": {"limit": 50}},
    {"method": "GET", "path": "/alumnos", "params": {"limit": 50, "periodo_id": 1}, "label": "GET /alumnos?periodo_id"},
    {"method": "GET", "path": "/asistencia", "params": {"limit": 50, "fecha": datetime.now().strftime("%Y-%m-%d")}},
    {"method": "GET", "path": "/matriculas", "params": {"limit": 50}},
    {"method": "GET", "path": "/pagos", "params": {"limit": 50}},
    {"method": "GET", "path": "/reportes/deudores", "params": {"limit": 50}},
    {"method": "GET", "path": "/reportes/tardanzas", "params": {"limit": 50, "fecha_inicio": "2026-01-01", "fecha_fin": "2026-12-31"}},
    {"method": "GET", "path": "/reportes/asistencia", "params": {"limit": 50, "periodo_id": 1}},
]


def get_auth_token(client: httpx.Client) -> Optional[str]:
    """Obtener JWT token de autenticación."""
    try:
        resp = client.post(
            f"{BASE_URL}/auth/login",
            data={"username": USERNAME, "password": PASSWORD},
        )
        if resp.status_code == 200:
            return resp.json()["access_token"]
        print(f"  ⚠ Login falló: {resp.status_code} - {resp.text[:200]}")
        return None
    except Exception as e:
        print(f"  ⚠ Error de conexión al login: {e}")
        return None


def percentile(data: List[float], p: float) -> float:
    """Calcular percentil."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return round(sorted_data[f], 2)
    return round(sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f]), 2)


def benchmark_endpoint(
    client: httpx.Client,
    method: str,
    path: str,
    params: Dict,
    headers: Dict,
    iterations: int,
) -> Dict[str, Any]:
    """Ejecutar benchmark contra un endpoint."""
    latencies = []
    payload_sizes = []
    errors = []
    def perform_request(i):
        nonlocal latencies, payload_sizes, errors
        try:
            start = time.perf_counter()
            if method == "GET":
                resp = client.get(f"{BASE_URL}{path}", params=params, headers=headers, timeout=30.0)
            elif method == "POST":
                resp = client.post(f"{BASE_URL}{path}", json=params, headers=headers, timeout=30.0)
            else:
                return
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

            latencies.append(elapsed_ms)
            payload_sizes.append(len(resp.content))
            
            # Print Request Id for tracing validation if present
            if "X-Request-Id" in resp.headers and i == 0:
                print(f" (Trace: {resp.headers['X-Request-Id']})", end="")

            if resp.status_code >= 400:
                errors.append({"iteration": i, "status": resp.status_code, "body": resp.text[:200]})
        except Exception as e:
            errors.append({"iteration": i, "error": str(e)})

    # Ejecutar peticiones concurrentemente para estresar el servidor
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(perform_request, range(iterations))

    if not latencies:
        return {
            "error": "No successful requests",
            "errors": errors,
        }

    return {
        "iterations": iterations,
        "successful": len(latencies),
        "errors_count": len(errors),
        "latency_p50_ms": percentile(latencies, 50),
        "latency_p95_ms": percentile(latencies, 95),
        "latency_p99_ms": percentile(latencies, 99),
        "latency_avg_ms": round(statistics.mean(latencies), 2),
        "latency_min_ms": round(min(latencies), 2),
        "latency_max_ms": round(max(latencies), 2),
        "payload_avg_bytes": round(statistics.mean(payload_sizes)) if payload_sizes else 0,
        "payload_max_bytes": max(payload_sizes) if payload_sizes else 0,
        "errors": errors if errors else None,
    }


def run_benchmark() -> Dict[str, Any]:
    """Ejecutar benchmark completo."""
    print(f"=" * 60)
    print(f"  BENCHMARK BASELINE - Sistema Musuq Cloud")
    print(f"  URL: {BASE_URL}")
    print(f"  Iterations per endpoint: {ITERATIONS}")
    print(f"  Timestamp: {datetime.now().isoformat()}")
    print(f"=" * 60)

    client = httpx.Client()

    # Autenticación
    print("\n📡 Obteniendo token de autenticación...")
    token = get_auth_token(client)
    if not token:
        print("❌ No se pudo obtener token. Abortando.")
        return {"error": "Auth failed"}
    headers = {"Authorization": f"Bearer {token}"}
    print("  ✅ Token obtenido\n")

    # Warmup (1 request por endpoint)
    print("🔥 Warmup...")
    for ep in CRITICAL_ENDPOINTS:
        try:
            client.get(f"{BASE_URL}{ep['path']}", params=ep.get("params", {}), headers=headers, timeout=15.0)
        except Exception:
            pass
    print("  ✅ Warmup completo\n")

    # Benchmark
    results = {}
    for ep in CRITICAL_ENDPOINTS:
        label = ep.get("label", f"{ep['method']} {ep['path']}")
        print(f"📊 Benchmarking {label} ...", end=" ", flush=True)

        result = benchmark_endpoint(
            client=client,
            method=ep["method"],
            path=ep["path"],
            params=ep.get("params", {}),
            headers=headers,
            iterations=ITERATIONS,
        )
        results[label] = result

        if "error" not in result or result.get("successful", 0) > 0:
            print(f"p50={result.get('latency_p50_ms', '?')}ms  p95={result.get('latency_p95_ms', '?')}ms  "
                  f"payload={result.get('payload_avg_bytes', '?')}B")
        else:
            print(f"❌ {result.get('error', 'Unknown error')}")

    client.close()

    # Generar informe
    report = {
        "benchmark_type": "baseline",
        "timestamp": datetime.now().isoformat(),
        "base_url": BASE_URL,
        "iterations_per_endpoint": ITERATIONS,
        "results": results,
    }

    # Guardar a archivo
    output_dir = os.path.join(os.path.dirname(__file__), "..", "benchmark_results")
    os.makedirs(output_dir, exist_ok=True)
    filename = f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_path = os.path.join(output_dir, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📁 Informe guardado en: {output_path}")

    # Resumen en consola
    print(f"\n{'='*60}")
    print(f"  RESUMEN BASELINE")
    print(f"{'='*60}")
    print(f"{'Endpoint':<40} {'p50':>8} {'p95':>8} {'Payload':>10}")
    print(f"{'-'*40} {'-'*8} {'-'*8} {'-'*10}")
    for label, r in results.items():
        if "latency_p50_ms" in r:
            print(f"{label:<40} {r['latency_p50_ms']:>6.1f}ms {r['latency_p95_ms']:>6.1f}ms "
                  f"{r['payload_avg_bytes']:>8}B")
    print(f"{'='*60}")

    return report


if __name__ == "__main__":
    run_benchmark()
