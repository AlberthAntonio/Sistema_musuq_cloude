# Bitacora Fase 3 - Integracion con modulo de horarios existente

Fecha: 2026-03-30
Estado de fase: APROBADA

## 1. Objetivo de fase
Conectar el modulo `horarios` con bloques de plantilla sin romper el uso legacy.

## 2. Cambios realizados
- Se extendieron schemas de horario para aceptar `plantilla_bloque_id`.
- Se reforzo `HorarioService` con validaciones de integracion:
  - valida existencia de `plantilla_bloque_id`.
  - rechaza asignaciones sobre bloques `RECREO` o `LIBRE`.
  - obliga consistencia de `dia_semana`, `hora_inicio`, `hora_fin`, `grupo`, `periodo`, `turno` y `aula_id` con la plantilla.
  - mantiene validacion de conflicto por grupo/docente.
- Se ajusto endpoint de horarios por aula para compatibilidad dual:
  - `GET /aulas/{id}/horarios` ahora acepta filtros opcionales `grupo` y `turno`.
  - cuando hay contexto de grupo (y plantilla disponible), retorna estructura dinamica basada en grilla final de plantilla.
  - si no hay plantilla, conserva fallback legacy sobre `horarios`.
- Se actualizo cliente/controlador desktop para consumir `grupo` en el endpoint de aula y mantener representacion legacy filtrando bloques no `CLASE`.

## 3. Archivos tocados
- backend/app/schemas/horario.py
- backend/app/services/horario_service.py
- backend/app/services/aula_service.py
- backend/app/api/routes/aulas.py
- backend/tests/test_horarios_plantillas_fase3.py
- desktop/core/api_client.py
- desktop/controllers/academico_controller.py

## 4. Validaciones ejecutadas
- Pruebas fase 3:
  - pytest -q tests/test_horarios_plantillas_fase3.py
  - Resultado: 4 passed
- No regresiones backend completas:
  - pytest -q
  - Resultado: 53 passed, 0 failed

## 5. Verificacion contra criterios de fase
- Crear horario con `plantilla_bloque_id` valido: CUMPLE
- Rechazar asignacion sobre RECREO/LIBRE: CUMPLE
- Flujos antiguos siguen funcionando temporalmente: CUMPLE

## 6. Riesgos abiertos
- La UI desktop todavia renderiza grilla de slots fijos (personalizacion visual total se aborda en fase 4).
- En aulas con multiples plantillas activas para distinto turno, el endpoint de aula por grupo toma la plantilla activa mas reciente si no se especifica turno.

## 7. Checklist DoD Fase 3
- Compatibilidad dual (viejo + nuevo): CUMPLE
- Tests de integracion horarios + plantilla: CUMPLE
- Estado final de fase: APROBADA

## 8. Conclusion
La Fase 3 queda cerrada con integracion backend/desktop en modo dual, validaciones de negocio para `plantilla_bloque_id` y sin regresiones en la suite backend.
