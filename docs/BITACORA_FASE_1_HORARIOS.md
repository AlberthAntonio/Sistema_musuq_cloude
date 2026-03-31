# Bitácora Fase 1 - Modelo de datos y migraciones

Fecha: 2026-03-30
Estado de fase: APROBADA

## 1. Objetivo de fase
Crear soporte estructural para plantillas de horario sin romper el modelo actual de horarios.

## 2. Cambios realizados
- Se agregaron nuevas entidades SQLAlchemy:
  - PlantillaHorario
  - PlantillaBloque
- Se agregó FK opcional en horarios:
  - horarios.plantilla_bloque_id (nullable)
- Se implementaron constraints base en bloques de plantilla:
  - dia_semana entre 1 y 6
  - hora_inicio < hora_fin
  - tipo_bloque en CLASE, RECREO, LIBRE
- Se agregaron índices de fase:
  - (plantilla_id, dia_semana, hora_inicio)
  - (aula_id, grupo, periodo, turno, activo)
- Se agregó servicio base para validaciones iniciales de plantillas.

## 3. Archivos tocados
- backend/app/models/plantilla_horario.py
- backend/app/models/horario.py
- backend/app/models/__init__.py
- backend/app/db/database.py
- backend/app/services/plantilla_horario_service.py
- backend/alembic/env.py
- backend/alembic/versions/20260330_f1a2b3c4d5e6_add_horario_template_tables.py
- backend/tests/test_horarios_plantillas_fase1.py

## 4. Validaciones ejecutadas
- Pruebas nuevas de fase:
  - pytest -q tests/test_horarios_plantillas_fase1.py
  - Resultado: 4 passed
- Migración Alembic:
  - alembic upgrade head
  - Resultado: upgrade aplicado hasta revision f1a2b3c4d5e6 sin errores
- Reversibilidad de migración:
  - alembic downgrade c7d9e1f2a3b4
  - alembic upgrade head
  - Resultado: downgrade y re-upgrade ejecutados sin errores
- No regresiones backend:
  - pytest -q
  - Resultado: 46 passed, 0 failed

## 5. Verificación contra criterios de fase
- alembic upgrade head funciona: CUMPLE
- insert de bloque valido funciona: CUMPLE
- insert con hora_fin <= hora_inicio falla: CUMPLE

## 6. Riesgos abiertos
- Aún no hay endpoints ni schemas para CRUD de plantillas (se aborda en fase 2).
- Integración UI dinámica con bloques reales todavía pendiente (fase 4).

## 7. Checklist DoD Fase 1
- Esquema listo: CUMPLE
- Migración reversible: CUMPLE
- Sin regresión en CRUD actual: CUMPLE

## 8. Conclusión
La Fase 1 queda cerrada. El backend ya dispone de base estructural para plantillas y de una ruta segura para continuar con Fase 2 (API y servicios de plantilla).
