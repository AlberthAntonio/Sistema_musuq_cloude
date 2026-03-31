# Bitácora Fase 5 - Backfill Horarios Legacy a Plantillas

## Estado
- APROBADA

## Objetivo
Migrar datos legacy de `horarios` al nuevo modelo de `plantilla_horario` + `plantilla_bloque` sin romper compatibilidad ni duplicar datos en re-ejecuciones.

## Implementación

### 1) Servicio de backfill idempotente
- Archivo: `backend/app/services/backfill_horarios_service.py`
- Función principal: `backfill_horarios_to_plantillas(...)`
- Reglas implementadas:
  - Resuelve `aula_id` desde `horario.aula_id` o por nombre (`horario.aula` -> `aula.nombre`).
  - Normaliza turno (`MAÑANA`/`MANANA` -> `MANANA`, etc.).
  - Crea plantilla por alcance: (`aula_id`, `grupo`, `periodo`, `turno`).
  - Crea bloque `CLASE` por slot (`dia_semana`, `hora_inicio`, `hora_fin`) si no existe.
  - Asigna `horarios.plantilla_bloque_id` cuando el mapeo es valido.
  - Reporta no mapeados con razones (`aula_no_resuelta`, `slot_conflict_non_clase`).
  - Soporta `dry_run` con rollback total.

### 2) Script ejecutable
- Archivo: `backend/scripts/backfill_horarios_fase5.py`
- Soporta:
  - `--dry-run`
  - `--sample-size`
  - `--detail-limit`
  - `--output`
- Genera reporte JSON y resumen por consola.

### 3) Registro de servicio
- Archivo: `backend/app/services/__init__.py`
- Exporta: `backfill_horarios_to_plantillas`.

## Pruebas

### Pruebas nuevas Fase 5
- Archivo: `backend/tests/test_backfill_horarios_fase5.py`
- Casos:
  - Crea plantilla + bloques + mapea horarios legacy.
  - Idempotencia en re-ejecución.
  - Reporte de no mapeados cuando aula no se puede resolver.

### Resultado de validación
- Suite backend completa:
  - `56 passed in 1.85s`
- Ejecución script en simulación:
  - Comando:
    - `python -m scripts.backfill_horarios_fase5 --dry-run --output benchmark_results/backfill_horarios_fase5_dryrun.json`
  - Resultado:
    - `total_horarios: 3`
    - `horarios_mapeados: 3`
    - `horarios_no_mapeados: 0`
    - `plantillas_creadas: 2`
    - `bloques_creados: 3`

## Notas operativas
- Para producción, ejecutar primero con `--dry-run` y revisar el JSON.
- Si el reporte es consistente, ejecutar sin `--dry-run` en ventana controlada.
- El proceso es idempotente: puede correrse nuevamente para cubrir nuevos horarios legacy.
