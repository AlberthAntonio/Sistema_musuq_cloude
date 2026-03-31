"""
Servicio de backfill para Fase 5 (horarios -> plantillas).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.aula import Aula
from app.models.horario import Horario
from app.models.plantilla_horario import PlantillaBloque, PlantillaHorario


def _normalize_turno(value: Optional[str]) -> str:
    if not value:
        return "MANANA"

    normalized = (
        value.strip()
        .upper()
        .replace("Á", "A")
        .replace("É", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ú", "U")
        .replace("Ñ", "N")
    )

    if "TAR" in normalized:
        return "TARDE"
    if "MAN" in normalized or "MAT" in normalized:
        return "MANANA"
    return normalized


def _resolve_aula_id(horario: Horario, aula_by_name: Dict[str, int]) -> Optional[int]:
    if horario.aula_id:
        return horario.aula_id

    if not horario.aula:
        return None

    return aula_by_name.get(horario.aula.strip().upper())


def backfill_horarios_to_plantillas(
    db: Session,
    *,
    dry_run: bool = True,
    sample_size: int = 30,
    detail_limit: int = 200,
) -> Dict[str, Any]:
    """
    Migra horarios legacy al nuevo modelo de plantillas.

    Reglas:
    - Idempotente: no duplica plantillas/bloques si ya existen.
    - Crea plantillas por alcance (aula_id, grupo, periodo, turno).
    - Crea bloques CLASE por slot unico (dia, hora_inicio, hora_fin).
    - Asigna horarios.plantilla_bloque_id cuando sea posible.
    - Reporta registros no mapeados con causa.
    """

    report: Dict[str, Any] = {
        "dry_run": dry_run,
        "total_horarios": 0,
        "total_horarios_con_plantilla": 0,
        "plantillas_creadas": 0,
        "bloques_creados": 0,
        "horarios_mapeados": 0,
        "horarios_ya_mapeados": 0,
        "horarios_no_mapeados": 0,
        "no_mapeados": [],
        "muestra_mapeados": [],
    }

    try:
        aulas = db.query(Aula).all()
        aula_by_name = {a.nombre.strip().upper(): a.id for a in aulas if a.nombre}

        horarios = db.query(Horario).order_by(Horario.id.asc()).all()
        report["total_horarios"] = len(horarios)

        # Cache de plantillas activas por alcance
        plantillas = db.query(PlantillaHorario).filter(PlantillaHorario.activo == True).all()
        plantilla_by_scope: Dict[Tuple[int, str, str, str], PlantillaHorario] = {}
        for plantilla in plantillas:
            key = (
                plantilla.aula_id,
                (plantilla.grupo or "").strip().upper(),
                (plantilla.periodo or "").strip().upper(),
                _normalize_turno(plantilla.turno),
            )
            current = plantilla_by_scope.get(key)
            if current is None or (plantilla.version, plantilla.id) > (current.version, current.id):
                plantilla_by_scope[key] = plantilla

        # Cache de bloques por plantilla y slot
        bloques = db.query(PlantillaBloque).all()
        bloque_by_slot: Dict[Tuple[int, int, str, str], PlantillaBloque] = {}
        for bloque in bloques:
            key = (bloque.plantilla_id, bloque.dia_semana, bloque.hora_inicio, bloque.hora_fin)
            current = bloque_by_slot.get(key)
            if current is None:
                bloque_by_slot[key] = bloque
            elif current.tipo_bloque != "CLASE" and bloque.tipo_bloque == "CLASE":
                bloque_by_slot[key] = bloque

        for horario in horarios:
            if horario.plantilla_bloque_id:
                report["horarios_ya_mapeados"] += 1
                report["total_horarios_con_plantilla"] += 1
                continue

            aula_id = _resolve_aula_id(horario, aula_by_name)
            if aula_id is None:
                report["horarios_no_mapeados"] += 1
                if len(report["no_mapeados"]) < detail_limit:
                    report["no_mapeados"].append(
                        {
                            "horario_id": horario.id,
                            "reason": "aula_no_resuelta",
                            "aula": horario.aula,
                            "aula_id": horario.aula_id,
                        }
                    )
                continue

            grupo = (horario.grupo or "").strip().upper()
            periodo = (horario.periodo or "2026-I").strip().upper()
            turno = _normalize_turno(horario.turno)

            scope = (aula_id, grupo, periodo, turno)
            plantilla = plantilla_by_scope.get(scope)
            if plantilla is None:
                plantilla = PlantillaHorario(
                    aula_id=aula_id,
                    grupo=grupo,
                    periodo=periodo,
                    turno=turno,
                    version=1,
                    activo=True,
                )
                db.add(plantilla)
                db.flush()
                plantilla_by_scope[scope] = plantilla
                report["plantillas_creadas"] += 1

            bloque_key = (plantilla.id, horario.dia_semana, horario.hora_inicio, horario.hora_fin)
            bloque = bloque_by_slot.get(bloque_key)
            if bloque is None:
                bloque = PlantillaBloque(
                    plantilla_id=plantilla.id,
                    dia_semana=horario.dia_semana,
                    hora_inicio=horario.hora_inicio,
                    hora_fin=horario.hora_fin,
                    tipo_bloque="CLASE",
                    etiqueta=None,
                    orden_visual=None,
                    activo=True,
                )
                db.add(bloque)
                db.flush()
                bloque_by_slot[bloque_key] = bloque
                report["bloques_creados"] += 1
            elif bloque.tipo_bloque != "CLASE":
                report["horarios_no_mapeados"] += 1
                if len(report["no_mapeados"]) < detail_limit:
                    report["no_mapeados"].append(
                        {
                            "horario_id": horario.id,
                            "reason": "slot_conflict_non_clase",
                            "plantilla_id": plantilla.id,
                            "bloque_id": bloque.id,
                            "tipo_bloque": bloque.tipo_bloque,
                        }
                    )
                continue

            horario.plantilla_bloque_id = bloque.id
            report["horarios_mapeados"] += 1
            report["total_horarios_con_plantilla"] += 1

            if len(report["muestra_mapeados"]) < sample_size:
                report["muestra_mapeados"].append(
                    {
                        "horario_id": horario.id,
                        "plantilla_id": plantilla.id,
                        "plantilla_bloque_id": bloque.id,
                        "aula_id": aula_id,
                        "grupo": grupo,
                        "periodo": periodo,
                        "turno": turno,
                        "dia_semana": horario.dia_semana,
                        "hora_inicio": horario.hora_inicio,
                        "hora_fin": horario.hora_fin,
                    }
                )

        if dry_run:
            db.rollback()
        else:
            db.commit()

        return report

    except Exception:
        db.rollback()
        raise
