# Acta de Despliegue - Fase 7 Horarios

Fecha: 2026-03-30
Alcance: Rollout gradual de horarios dinamicos por plantilla
Responsable tecnico: Equipo Backend

## 1. Cambios incluidos en release
1. Feature flag global para habilitar/deshabilitar horarios por plantilla.
2. Allowlist por `aula_id` para despliegue canary.
3. Headers de respuesta para observabilidad de modo:
   - `X-Horarios-Mode`
   - `X-Horarios-Rollout-Reason`
4. Pruebas automatizadas de rollout y fallback legacy.
5. Script de monitoreo inicial en tiempo de despliegue.

## 2. Preparacion previa
1. Confirmar migraciones al dia (`alembic upgrade head`).
2. Confirmar pruebas backend en verde (`pytest -q`).
3. Configurar entorno:
   - `HORARIOS_PLANTILLAS_ENABLED=true`
   - `HORARIOS_PLANTILLAS_ALLOW_AULAS=<ids canary>`
4. Reiniciar servicio backend.

## 3. Plan de despliegue gradual
1. Etapa 1 (canary): habilitar 1-2 aulas de baja criticidad.
2. Etapa 2 (expansion): ampliar allowlist a 20-40% de aulas.
3. Etapa 3 (general): usar `HORARIOS_PLANTILLAS_ALLOW_AULAS=*`.

Criterio para avanzar de etapa:
- Sin 5xx criticos en endpoints de horarios.
- p95 dentro del umbral operativo.
- Sin incidencias funcionales en feedback inicial de usuarios.

## 4. Monitoreo operativo recomendado
1. Ejecutar:
   - `python -m scripts.monitor_horarios_rollout_fase7`
2. Revisar reporte en:
   - `backend/benchmark_results/monitor_horarios_rollout_fase7_*.json`
3. Verificar en API para aulas piloto:
   - `X-Horarios-Mode=dynamic`
   - `X-Horarios-Rollout-Reason=enabled_allowlist_aula`

## 5. Plan de rollback inmediato
Rollback funcional (sin rollback de esquema):
1. Ajustar entorno:
   - `HORARIOS_PLANTILLAS_ENABLED=false`
2. Reiniciar backend.
3. Verificar que endpoint de aulas retorna:
   - `X-Horarios-Mode=legacy`
   - `X-Horarios-Rollout-Reason=feature_flag_disabled`
4. Registrar incidente y evidencia en bitacora operativa.

## 6. Resultado de validacion previa
1. Pruebas focales Fase 7: 6 passed.
2. Suite backend completa: 61 passed.
3. Errores estaticos en cambios de fase: sin hallazgos.

## 7. Aprobacion
Estado: APROBADO PARA PILOTO CONTROLADO
Condicion: ejecutar ventana piloto y registrar evidencia de KPIs en produccion.
