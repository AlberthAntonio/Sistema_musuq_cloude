# Bitácora Fase 0 - Horarios Escalables

Fecha: 2026-03-30
Estado de fase: APROBADA

## 1. Objetivo de fase
Dejar una línea base técnica y funcional antes de iniciar cambios de arquitectura en el módulo de horarios.

## 2. Alcance ejecutado
- Revisión del estado actual de código de horarios en backend y desktop.
- Verificación de pruebas backend sugeridas en el plan y suite completa.
- Smoke técnico de arranque de API y carga de módulo desktop.

## 3. Hallazgos de baseline
- El backend de horarios sigue en modelo clásico (sin entidades de plantilla):
  - Solo existe tabla/entidad `horarios`.
  - No existen `plantillas_horario` ni `plantilla_bloques`.
  - No hay campo `plantilla_bloque_id` en `horarios`.
- La UI desktop de horarios sigue rígida por slots fijos:
  - `obtener_slots_horarios` devuelve bloques hardcodeados.
  - Recreo sigue hardcodeado en el grid.
  - `DialogoHorario` crea clases sobre slots fijos, no sobre bloques dinámicos.

## 4. Validaciones ejecutadas

### 4.1 Pruebas backend (focales)
- Comando: `pytest -q tests/test_health.py`
- Resultado: 3 passed

- Comando: `pytest -q tests/test_alumnos_periodos.py`
- Resultado: 9 passed

### 4.2 Pruebas backend (suite completa)
- Comando: `pytest -q`
- Resultado: 42 passed, 0 failed

### 4.3 Smoke técnico
- API:
  - Comando: `python -m uvicorn main:app --host 127.0.0.1 --port 8010`
  - Resultado: arranque correcto, startup completo, servidor escuchando.
- Desktop:
  - Comando: `python -c "import main; print('desktop_import_ok')"`
  - Resultado: `desktop_import_ok`.

## 5. Riesgos abiertos
- Worktree con muchos cambios en curso no relacionados a horarios; se requiere aislar cambios de próximas fases solo en archivos del módulo de horarios para evitar regresiones cruzadas.

## 6. Checklist DoD Fase 0
- Baseline documentado y reproducible: CUMPLE

## 7. Conclusión
La fase 0 queda cerrada con baseline técnico validado. El sistema está listo para iniciar Fase 1 (modelo de datos y migraciones) bajo esquema incremental y con pruebas por gate.
