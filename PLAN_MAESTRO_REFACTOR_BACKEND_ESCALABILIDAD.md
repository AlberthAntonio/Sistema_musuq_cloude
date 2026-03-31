# PLAN MAESTRO DE REFACTOR BACKEND Y ESCALABILIDAD

## 1) Proposito del documento
Este documento esta disenado para entregarse a una IA de desarrollo y ejecutar una refactorizacion completa, profesional y medible del backend para:
- Mantener operacion actual para una sola institucion.
- Preparar la plataforma para escalar a alto volumen sin degradacion.
- Reducir latencia de consultas y consumo de red.
- Dejar base tecnica lista para evolucion futura a multiinstitucion.

Este documento contiene contexto, decisiones tecnicas, backlog ejecutable, reglas de implementacion, criterios de aceptacion y prompts listos para uso.

---

## 2) Estado actual resumido
- Backend en FastAPI + SQLAlchemy + Alembic.
- Dominio academico completo: alumnos, matriculas, pagos, asistencia, docentes, aulas, cursos, periodos.
- Filtrado por periodo existe, pero no siempre obligatorio.
- Riesgo de crecimiento por tablas de alto volumen: asistencias, pagos, reportes.
- Riesgo de latencia por consultas sin estrategia uniforme de indices compuestos y sin estandar de payload minimo.

---

## 3) Objetivos no funcionales (SLO/SLI)
Definir como objetivos minimos en produccion:
1. Latencia p50 de endpoints criticos <= 150 ms.
2. Latencia p95 de endpoints criticos <= 450 ms.
3. Latencia p99 de endpoints criticos <= 900 ms.
4. Error rate 5xx < 0.5% diario.
5. Tiempo de reportes pesados asincronos <= 60 s para datasets medios.
6. Disponibilidad mensual >= 99.9%.
7. Uso promedio de CPU API <= 65% en horario pico.
8. Saturacion del pool de conexiones DB < 80% sostenido.

Endpoints criticos:
- GET /alumnos
- GET /asistencia
- POST /asistencia
- GET /matriculas
- GET /pagos
- GET /reportes/deudores

---

## 4) Principios de arquitectura
1. Consulta minima necesaria: traer solo campos requeridos por vista.
2. Filtros obligatorios por contexto operativo (periodo, estado, fecha) en endpoints de alto volumen.
3. Paginacion obligatoria en todo listado.
4. Reporteria pesada fuera del request sincrono.
5. Observabilidad primero: no optimizar a ciegas.
6. Cambios incrementales con rollback seguro.
7. Sin romper contrato de API existente salvo versionado explicito.

---

## 5) Alcance del refactor (in scope)
1. Estandarizar consultas y filtros en servicios y rutas.
2. Redisenar estrategia de indices y constraints.
3. Estandarizar paginacion, ordenamiento, filtros y proyeccion de campos.
4. Reducir payload y mejorar serializacion.
5. Introducir cache selectiva en lecturas repetitivas.
6. Mover reportes pesados a ejecucion asincrona.
7. Instrumentar metricas, logs estructurados y trazas.
8. Definir pruebas de carga automatizables.
9. Fortalecer migraciones Alembic como fuente unica de cambios de esquema.

## 6) Fuera de alcance (por ahora)
1. Multiinstitucion productivo completo.
2. Reescritura total a arquitectura de microservicios.
3. Cambio total de ORM o framework.

---

## 7) Modelo de datos objetivo (single institution robusto)

### 7.1 Reglas generales
1. Toda tabla transaccional debe tener:
- id PK
- created_at
- updated_at
- created_by (cuando aplique)
- estado (si el dominio lo requiere)

2. Toda entidad de alto volumen debe tener indices por:
- periodo_id
- fecha o rango temporal
- estado
- foreign keys de consulta frecuente

3. Evitar nulls en claves de contexto cuando el dominio lo exige.
Ejemplo: asistencia.periodo_id debe migrar a NOT NULL despues de saneamiento.

### 7.2 Constraints recomendados
1. Matricula:
- UNIQUE (alumno_id, periodo_id, estado_activo_logico)
- CHECK estado IN ('activo','retirado')

2. Asistencia:
- UNIQUE (alumno_id, fecha, turno)
- CHECK estado IN ('PUNTUAL','TARDANZA','INASISTENCIA')
- CHECK turno IN ('MANANA','TARDE')

3. Pago:
- indice compuesto por (matricula_id, fecha_pago desc)
- indice por (estado, fecha_vencimiento)

4. Periodo:
- regla de unicidad por nombre vigente.

### 7.3 Indices compuestos sugeridos
1. asistencias(periodo_id, fecha desc, estado)
2. asistencias(alumno_id, fecha desc)
3. matriculas(periodo_id, estado, grupo)
4. pagos(periodo_id derivado via matricula, fecha_pago desc) si existe desnormalizacion controlada
5. obligaciones(matricula_id, estado, fecha_vencimiento)
6. alumnos(activo, apell_paterno, apell_materno)

Nota: Validar cada indice con EXPLAIN ANALYZE antes y despues.

---

## 8) Estandar de API para rendimiento

### 8.1 Paginacion obligatoria
Todos los listados deben soportar:
- limit (default 50, max 200)
- offset o cursor
- total_count opcional por parametro include_total=true

### 8.2 Filtros obligatorios en alto volumen
Para endpoints de asistencia y reportes:
- requerir rango de fechas o periodo_id.
- rechazar consultas abiertas sin filtro en produccion.

### 8.3 Proyeccion de campos
Agregar parametro fields=campo1,campo2 cuando sea viable.
Si no se implementa fields, crear endpoints resumen separados para grillas.

### 8.4 Estandar de respuesta
Formato uniforme:
- data: []
- meta: {limit, offset, total, has_next, request_id}

### 8.5 Compresion y red
- Activar gzip o brotli.
- Evitar enviar blobs/base64 en listados.
- Para reportes grandes, entregar URL de descarga asincrona.

---

## 9) Refactor de capa servicio y repositorio

### 9.1 Objetivo
Reducir N+1, centralizar filtros y evitar duplicacion de logica SQL.

### 9.2 Acciones
1. Introducir capa repository por agregado:
- AlumnoRepository
- AsistenciaRepository
- MatriculaRepository
- PagoRepository

2. Mover construccion de query a repositorios con metodos reutilizables.

3. En servicios, dejar solo reglas de negocio.

4. Definir QuerySpec por caso de uso:
- filtros
- orden
- paginacion
- proyeccion

5. Aplicar selectinload/joinedload solo cuando sea necesario.

---

## 10) Reporteria y procesos pesados

### 10.1 Problema
Reportes complejos en tiempo real compiten con transacciones del dia.

### 10.2 Solucion
1. Crear cola de jobs (RQ/Celery/Arq segun stack elegido).
2. Endpoint de reporte inicia job y retorna job_id.
3. Endpoint de estado devuelve progreso.
4. Endpoint de descarga entrega resultado final.
5. Mantener cache de reportes recientes por parametros.

---

## 11) Cache y estrategia de invalidez

### 11.1 Candidatos a cache
1. Catalogos: cursos, aulas, configuraciones.
2. Dashboard ejecutivo por periodo.
3. Listados con filtros repetitivos.

### 11.2 Reglas
1. TTL corto para datos operativos (30-120 s).
2. Invalidez por evento de escritura.
3. Nunca cachear datos de autenticacion sensible.

---

## 12) Conexion a base de datos y concurrencia

### 12.1 SQLAlchemy engine/pool
Configurar segun entorno:
- pool_size
- max_overflow
- pool_timeout
- pool_recycle
- pool_pre_ping

### 12.2 Riesgos a controlar
1. Agotamiento de conexiones.
2. Transacciones largas.
3. Bloqueos por updates concurrentes.

### 12.3 Reglas
1. Transaccion corta.
2. Commits puntuales.
3. Reintentos con backoff en errores transitorios.

---

## 13) Observabilidad obligatoria

### 13.1 Logging
1. Log estructurado JSON.
2. request_id en toda respuesta.
3. Log de latencia por endpoint.

### 13.2 Metricas
Exponer /metrics (Prometheus):
1. request_count por endpoint/status.
2. request_latency histogram.
3. db_query_duration histogram.
4. pool_in_use y pool_wait_time.
5. cache_hit_ratio.

### 13.3 Trazas
Instrumentar OpenTelemetry para correlacion API -> DB.

---

## 14) Seguridad y robustez
1. Rate limiting por endpoint sensible.
2. Validacion estricta de payloads.
3. Limite de tamano de request body.
4. Sanitizacion de filtros de orden/campos.
5. Politica consistente de errores (sin filtrar internals).

---

## 15) Plan de migracion por fases

### Fase 0 (1 semana) - Baseline
1. Medir estado actual con metricas base.
2. Capturar top 20 queries mas costosas.
3. Ejecutar pruebas de carga baseline.

Entregables:
- Informe de baseline.
- Lista priorizada de cuellos.

### Fase 1 (2 a 3 semanas) - Quick wins
1. Paginacion obligatoria + limites maximos.
2. Filtros obligatorios en endpoints de alto volumen.
3. Indices compuestos de mayor impacto.
4. Reduccion de payloads en listados.

Entregables:
- Migraciones Alembic.
- Cambios en rutas/servicios.
- Comparativa antes/despues p95.

### Fase 2 (3 a 5 semanas) - Estructural
1. Repository layer + QuerySpec.
2. Cache selectiva.
3. Jobs asincronos para reportes.

Entregables:
- Modulos nuevos de repositorio y jobs.
- Dashboards de metricas.

### Fase 3 (2 a 4 semanas) - Hardening
1. Trazas distribuidas.
2. Politicas de retry/circuit breaker interno.
3. Pruebas de estres y caos controlado.

Entregables:
- SLO cumplidos.
- Runbooks de operacion.

---

## 16) Criterios de aceptacion (Definition of Done)
1. Ningun endpoint de listado sin paginacion.
2. Endpoints de alto volumen exigen filtros de contexto.
3. p95 mejora minima de 30% en endpoints criticos.
4. Query count por request reducido en al menos 40% en pantallas clave.
5. Payload medio reducido en al menos 35% en listados.
6. 0 regresiones funcionales en pruebas de integracion.
7. Migraciones reproducibles en entorno limpio.
8. Dashboard de metricas operativo.

---

## 17) Backlog tecnico ejecutable (tickets)

### EPIC A - Rendimiento SQL
A1. Inventariar consultas lentas por endpoint.
A2. Agregar indices compuestos priorizados.
A3. Reescribir consultas con planes ineficientes.
A4. Agregar validaciones para evitar full scans por consultas abiertas.

### EPIC B - Contratos de API
B1. Estandarizar paginacion global.
B2. Estandarizar meta de respuesta.
B3. Reducir campos por DTO de lista y detalle.
B4. Limitar include_total por defecto.

### EPIC C - Arquitectura backend
C1. Introducir repositories por dominio.
C2. Separar business rules de acceso a datos.
C3. Implementar QuerySpec reutilizable.
C4. Revisar uso de eager loading.

### EPIC D - Reportes y asincronia
D1. Definir framework de jobs.
D2. Migrar reportes pesados a jobs.
D3. Persistir resultados de reporte y expiracion.
D4. Endpoint de estado y descarga.

### EPIC E - Observabilidad y operacion
E1. Metricas Prometheus.
E2. Trazas OTel.
E3. Alertas de latencia y errores.
E4. Runbook de incidentes.

---

## 18) Pruebas requeridas

### 18.1 Unitarias
- Servicios con mocks de repositorio.
- Validaciones de filtros y paginacion.

### 18.2 Integracion
- Endpoints criticos con DB real de test.
- Verificacion de indices y planes de consulta.

### 18.3 Carga
Escenarios:
1. Hora pico asistencia (concurrencia alta escritura).
2. Cierre de caja (lectura + escritura pagos).
3. Consulta dashboard masiva simultanea.

Herramientas sugeridas:
- k6 o Locust.

Criterios:
- No timeouts masivos.
- p95 dentro de SLO.

---

## 19) Riesgos y mitigacion
1. Riesgo: romper endpoints usados por desktop.
Mitigacion: compatibilidad hacia atras y pruebas de contrato.

2. Riesgo: indices afectan escritura.
Mitigacion: medir costo de write y aplicar solo indices con beneficio real.

3. Riesgo: cache sirviendo datos stale.
Mitigacion: TTL corto + invalidez por evento.

4. Riesgo: migraciones largas en produccion.
Mitigacion: migraciones online, ventanas planificadas y rollback.

---

## 20) Prompt maestro para IA (copiar y usar)

Eres un arquitecto senior de backend Python/FastAPI/SQLAlchemy con foco en rendimiento y escalabilidad.
Tu tarea es ejecutar una refactorizacion completa del backend siguiendo estrictamente el documento PLAN_MAESTRO_REFACTOR_BACKEND_ESCALABILIDAD.md.

Objetivo:
- Mantener funcionalidad actual.
- Mejorar latencia y throughput.
- Reducir consumo de red.
- Dejar base lista para futura multiinstitucion sin activarla aun.

Reglas obligatorias:
1. No romper contratos existentes sin versionado.
2. Implementar por fases con commits pequenos.
3. Cada cambio debe incluir prueba automatizada.
4. Todo cambio de esquema debe ir por Alembic.
5. Medir antes y despues con evidencia numerica.

Entregables minimos:
1. Cambios de codigo backend completos.
2. Migraciones Alembic.
3. Pruebas unitarias/integracion/carga.
4. Dashboard de metricas y guia de operacion.
5. Informe final con:
- endpoints optimizados
- latencias antes/despues
- queries antes/despues
- payload antes/despues
- riesgos residuales

Orden de ejecucion:
1. Baseline y medicion.
2. Quick wins (paginacion, filtros, indices, payload).
3. Refactor estructural (repositorios + QuerySpec).
4. Reportes asincronos + cache.
5. Observabilidad completa.
6. Validacion final contra SLO.

Criterio de exito:
- Cumplir Definition of Done del plan.

---

## 21) Prompt de control de calidad para IA revisora
Actua como auditor tecnico externo.
Revisa que la implementacion cumpla este plan al 100%.
No aceptes respuestas sin evidencia medible.
Devuelve:
1. Hallazgos criticos.
2. Hallazgos altos.
3. Hallazgos medios.
4. Lista de faltantes exactos.
5. Veredicto final: APROBADO o NO APROBADO.

---

## 22) Checklist final de entrega
1. Baseline documentado.
2. Migraciones aplicadas y probadas.
3. Endpoints criticos optimizados.
4. Reportes pesados asincronos.
5. Cache operativa en lecturas repetitivas.
6. Metricas y trazas activas.
7. Pruebas de carga con resultados.
8. SLO cumplidos en entorno de preproduccion.
9. Manual de despliegue y rollback.
10. Informe final tecnico y ejecutivo.

Fin del documento.
