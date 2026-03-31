"""
Script de backfill Fase 5 para migrar horarios legacy hacia plantillas.

Uso:
    python -m scripts.backfill_horarios_fase5 --dry-run
    python -m scripts.backfill_horarios_fase5 --output benchmark_results/backfill_fase5.json
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from app.db.database import SessionLocal
from app.services.backfill_horarios_service import backfill_horarios_to_plantillas


def _build_default_output_path() -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("benchmark_results") / f"backfill_horarios_fase5_{ts}.json"


def _print_summary(report: Dict[str, Any]) -> None:
    print("=== FASE 5 BACKFILL HORARIOS -> PLANTILLAS ===")
    print(f"dry_run: {report['dry_run']}")
    print(f"total_horarios: {report['total_horarios']}")
    print(f"total_horarios_con_plantilla: {report['total_horarios_con_plantilla']}")
    print(f"plantillas_creadas: {report['plantillas_creadas']}")
    print(f"bloques_creados: {report['bloques_creados']}")
    print(f"horarios_mapeados: {report['horarios_mapeados']}")
    print(f"horarios_ya_mapeados: {report['horarios_ya_mapeados']}")
    print(f"horarios_no_mapeados: {report['horarios_no_mapeados']}")
    print(f"muestra_mapeados: {len(report['muestra_mapeados'])}")
    print(f"no_mapeados_detalle: {len(report['no_mapeados'])}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill de horarios legacy a plantillas (Fase 5)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ejecuta simulacion y revierte cambios al final.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=30,
        help="Cantidad de ejemplos mapeados a incluir en la muestra.",
    )
    parser.add_argument(
        "--detail-limit",
        type=int,
        default=200,
        help="Maximo de no mapeados detallados en el reporte.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Ruta de salida del reporte JSON.",
    )
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else _build_default_output_path()

    db = SessionLocal()
    try:
        report = backfill_horarios_to_plantillas(
            db,
            dry_run=args.dry_run,
            sample_size=args.sample_size,
            detail_limit=args.detail_limit,
        )
    finally:
        db.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    _print_summary(report)
    print(f"reporte_json: {output_path}")


if __name__ == "__main__":
    main()
