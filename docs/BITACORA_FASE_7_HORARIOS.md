# Bitacora Fase 7 - Rollout gradual y cierre

Fecha: 2026-03-30
Estado de fase: APROBADA (entorno QA/pre-produccion)

## 1. Objetivo de fase
Activar la funcionalidad de horarios dinamicos por plantillas con bajo riesgo operativo mediante feature flags, observabilidad de modo y plan de rollback inmediato.

## 2. Cambios realizados

### 2.1 Feature flags de rollout
- Archivo modificado: `backend/app/core/config.py`
- Settings agregados:
  - `HORARIOS_PLANTILLAS_ENABLED` (bool)
  - `HORARIOS_PLANTILLAS_ALLOW_AULAS` (CSV de aula_id o `*`)
  - `horarios_plantillas_allow_aulas_set` (parser de allowlist)

### 2.2 Configuracion operativa de entorno
- Archivo modificado: `backend/.env.example`
- Variables de entorno documentadas para activacion global, canary por aula y rollback.

### 2.3 Gating dynamic/legacy por aula
- Archivo modificado: `backend/app/services/aula_service.py`
- Cambios clave:
  - Evaluacion de rollout por aula (`_rollout_horarios_dinamicos`).
  - Metodo `obtener_horarios_aula_con_modo` con salida: lista + modo + razon.
  - Fallback automatico a modo legacy cuando corresponde.
  - Logging estructurado de modo aplicado y razon.

### 2.4 Observabilidad de rollout por headers
- Archivo modificado: `backend/app/api/routes/aulas.py`
- Endpoint `GET /aulas/{aula_id}/horarios` ahora expone:
  - `X-Horarios-Mode`: `dynamic` o `legacy`
  - `X-Horarios-Rollout-Reason`: motivo del enrutamiento de modo

### 2.5 Pruebas especificas de rollout
- Archivo nuevo: `backend/tests/test_horarios_rollout_fase7.py`
- Cobertura agregada:
  - Flag global OFF fuerza `legacy` y razon `feature_flag_disabled`.
  - Allowlist por aula habilita `dynamic` solo para aulas permitidas.
  - Verificacion de headers de rollout y comportamiento fallback.

### 2.6 Monitoreo inicial operativo
- Archivo nuevo: `backend/scripts/monitor_horarios_rollout_fase7.py`
- Script para:
  - Consultar `GET /metrics/summary`.
  - Verificar KPIs por endpoint (p95 y error rate 5xx).
  - Muestrear headers de rollout por `aula_id` configurada.
  - Emitir reporte JSON en `backend/benchmark_results/`.

## 3. Validaciones ejecutadas

### 3.1 Pruebas focales de rollout y regresion
- Comando:
  - `pytest -q tests/test_horarios_rollout_fase7.py tests/test_horarios_plantillas_fase3.py`
- Resultado:
  - `6 passed in 0.69s`

### 3.2 Suite completa backend
- Comando:
  - `pytest -q`
- Resultado:
  - `61 passed in 2.14s`

### 3.3 Verificacion de errores estaticos
- Resultado:
  - Sin errores en archivos modificados de config, servicios, rutas, tests y script de monitoreo.

## 4. Verificacion contra criterios de fase
- Activacion por feature flag modulo/sede (aula): CUMPLE
- Monitoreo inicial de errores y KPI listo: CUMPLE
- Rollback operativo documentado: CUMPLE
- Compatibilidad legacy mantenida: CUMPLE

## 5. Riesgos abiertos
1. Validacion de ventana piloto en produccion aun no ejecutada en este entorno.
2. Ajuste fino de umbrales de alerta (p95/error_rate) segun trafico real.

## 6. Checklist DoD Fase 7
- Feature flag y canary por aula: CUMPLE
- Observabilidad de modo rollout: CUMPLE
- Pruebas de comportamiento dynamic/legacy: CUMPLE
- Plan de rollback operativo: CUMPLE

## 7. Conclusion
La Fase 7 queda cerrada a nivel tecnico en entorno de QA/pre-produccion, con despliegue gradual controlado, fallback legacy y monitoreo operativo listos para piloto productivo.
