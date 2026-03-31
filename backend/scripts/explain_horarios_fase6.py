"""
Verificacion de indices con EXPLAIN QUERY PLAN para consultas clave de horarios/plantillas.

Ejecucion:
    python -m scripts.explain_horarios_fase6
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy import text

from app.db.database import engine


QUERIES = {
    "plantilla_lookup_alcance": (
        """
        EXPLAIN QUERY PLAN
        SELECT id, aula_id, grupo, periodo, turno, version
        FROM plantillas_horario
        WHERE aula_id = :aula_id
          AND grupo = :grupo
          AND periodo = :periodo
          AND turno = :turno
          AND activo = 1
        ORDER BY version DESC, id DESC
        LIMIT 1
        """,
        {"aula_id": 1, "grupo": "A", "periodo": "2026-I", "turno": "MANANA"},
    ),
    "bloques_por_plantilla": (
        """
        EXPLAIN QUERY PLAN
        SELECT id, plantilla_id, dia_semana, hora_inicio, hora_fin
        FROM plantilla_bloques
        WHERE plantilla_id = :plantilla_id
          AND activo = 1
        ORDER BY dia_semana, hora_inicio, orden_visual
        """,
        {"plantilla_id": 1},
    ),
    "horarios_por_bloque_grupo_periodo": (
        """
        EXPLAIN QUERY PLAN
        SELECT id, plantilla_bloque_id, grupo, periodo
        FROM horarios
        WHERE plantilla_bloque_id = :bloque_id
          AND grupo = :grupo
          AND periodo = :periodo
          AND activo = 1
        """,
        {"bloque_id": 1, "grupo": "A", "periodo": "2026-I"},
    ),
}


def _extract_plan_rows(rows: List[Any]) -> List[Dict[str, Any]]:
    result = []
    for row in rows:
        result.append(
            {
                "id": row[0],
                "parent": row[1],
                "notused": row[2],
                "detail": row[3],
            }
        )
    return result


def _detect_index_usage(plan_rows: List[Dict[str, Any]]) -> bool:
    details = " ".join((row.get("detail") or "").upper() for row in plan_rows)
    return "USING INDEX" in details or "USING COVERING INDEX" in details


def run() -> Dict[str, Any]:
    results: Dict[str, Any] = {}

    with engine.connect() as conn:
        for query_name, (sql, params) in QUERIES.items():
            rows = conn.execute(text(sql), params).fetchall()
            plan_rows = _extract_plan_rows(rows)
            results[query_name] = {
                "uses_index": _detect_index_usage(plan_rows),
                "plan": plan_rows,
            }

    uses_index_all = all(item["uses_index"] for item in results.values())

    report = {
        "report_type": "fase6_explain_indices_horarios",
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "verifications": {
            "todas_consultas_con_indice": uses_index_all,
        },
    }

    output_dir = Path(__file__).resolve().parent.parent / "benchmark_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"explain_horarios_fase6_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=== EXPLAIN FASE 6 HORARIOS ===")
    for query_name, data in results.items():
        print(f"{query_name} | uses_index={data['uses_index']}")
    print(f"reporte_json: {output_path}")

    return report


if __name__ == "__main__":
    run()
