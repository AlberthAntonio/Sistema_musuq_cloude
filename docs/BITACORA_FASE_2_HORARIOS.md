# Bitácora Fase 2 - API y servicios de plantilla

Fecha: 2026-03-30
Estado de fase: APROBADA

## 1. Objetivo de fase
Exponer API robusta para CRUD de plantillas y bloques, con validaciones anti-solape por día y endpoint de grilla final.

## 2. Cambios realizados
- Se crearon schemas Pydantic para plantillas, bloques, batch-upsert y grilla final.
- Se amplió el servicio de plantillas con CRUD completo:
  - Plantillas: listar, crear, actualizar, eliminar.
  - Bloques: listar, crear, actualizar, eliminar.
  - Batch-upsert de bloques.
  - Validaciones anti-solape por día.
  - Endpoint lógico de obtención de grilla final por aula+grupo+periodo+turno.
- Se implementaron rutas API nuevas:
  - GET /plantillas-horario/
  - POST /plantillas-horario/
  - PUT /plantillas-horario/{id}
  - DELETE /plantillas-horario/{id}
  - GET /plantillas-horario/{id}/bloques
  - POST /plantillas-horario/{id}/bloques
  - PUT /plantilla-bloques/{id}
  - DELETE /plantilla-bloques/{id}
  - POST /plantillas-horario/{id}/bloques/batch-upsert
  - GET /plantillas-horario/grilla-final
- Se registró el router en main para exponer endpoints de fase 2.
- Se preservó compatibilidad de servicio con firma legacy de fase 1 para evitar regresiones.

## 3. Archivos tocados
- backend/app/schemas/plantilla_horario.py
- backend/app/schemas/__init__.py
- backend/app/services/plantilla_horario_service.py
- backend/app/services/__init__.py
- backend/app/api/routes/plantilla_horarios.py
- backend/main.py
- backend/tests/test_plantillas_horario_api_fase2.py

## 4. Validaciones ejecutadas
- Pruebas API fase 2:
  - pytest -q tests/test_plantillas_horario_api_fase2.py
  - Resultado: 3 passed
- Compatibilidad fase 1 + fase 2:
  - pytest -q tests/test_horarios_plantillas_fase1.py tests/test_plantillas_horario_api_fase2.py
  - Resultado: 7 passed
- No regresiones backend completas:
  - pytest -q
  - Resultado: 49 passed, 0 failed
- Estado de migraciones:
  - alembic upgrade head
  - Resultado: esquema en head sin errores

## 5. Verificación contra criterios de fase
- API de plantillas operativa: CUMPLE
- Validaciones anti-solape por día: CUMPLE
- Respuestas de error claras 400/422 en conflictos/validación: CUMPLE

## 6. Riesgos abiertos
- Integración del módulo legacy de horarios con plantilla_bloque_id pendiente (fase 3).
- UI desktop aún consume slots fijos legacy (fase 4).

## 7. Checklist DoD Fase 2
- Servicios y rutas nuevas: CUMPLE
- Tests backend fase 2: CUMPLE
- Estado final de fase: APROBADA

## 8. Conclusión
La Fase 2 queda cerrada. La API de plantillas está activa y validada para continuar con Fase 3 (integración con módulo de horarios existente en compatibilidad dual).
