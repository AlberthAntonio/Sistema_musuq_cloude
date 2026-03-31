# PLAN FASEADO PARA HORARIOS ESCALABLES (EJECUCION POR IA)

## 1) Proposito del documento
Este documento esta disenado para entregar a una IA de desarrollo y ejecutar la mejora del modulo de horarios por fases, con control de errores y validaciones estrictas.

Objetivo principal:
- Permitir horarios 100% personalizables por dia (horas variables, multiples recreos, dias con pocas o muchas horas).
- Mantener compatibilidad con el sistema actual.
- Implementar una arquitectura escalable para crecimiento futuro.

---

## 2) Resultado de arquitectura recomendado
Aplicar arquitectura de 2 capas:
1. Plantilla de jornada (estructura del tiempo): bloques por aula/grupo/periodo/turno.
2. Asignacion academica (contenido): curso/docente sobre bloques de tipo CLASE.

Beneficios:
- El horario deja de depender de slots hardcodeados.
- Se pueden definir recreos ilimitados.
- Se puede tener un dia con 1 sola hora o con 10 bloques.
- Se mantiene trazabilidad y evolucion por periodo.

---

## 3) Alcance funcional
### In scope
1. Bloques configurables por dia y turno.
2. Tipos de bloque: CLASE, RECREO, LIBRE.
3. Validaciones anti-solapamiento en backend.
4. Vista desktop consumiendo bloques reales desde API.
5. Dialogos para crear/editar/eliminar bloques de plantilla.
6. Asignar curso/docente solo a bloques CLASE.
7. Pruebas por fase y gates de calidad.

### Out of scope (por ahora)
1. Drag and drop visual avanzado.
2. Reescritura total de todo el modulo academico.
3. Cambios masivos en otros dominios no relacionados.

---

## 4) Mapa de codigo actual (base de trabajo)
### Desktop
- `desktop/controllers/academico_controller.py` (slots fijos actuales)
- `desktop/ui/views/docentes/horarios_view.py` (grid + recreo hardcodeado)
- `desktop/ui/views/docentes/dialogo_horario.py` (alta de clase en slot fijo)
- `desktop/core/api_client.py` (cliente de horarios)

### Backend
- `backend/app/models/horario.py`
- `backend/app/schemas/horario.py`
- `backend/app/services/horario_service.py`
- `backend/app/api/routes/horarios.py`
- `backend/alembic/` (migraciones)

---

## 5) Reglas globales obligatorias para la IA
1. No romper endpoints existentes sin compatibilidad temporal.
2. No eliminar columnas o tablas usadas en produccion en fases tempranas.
3. Toda fase debe cerrar con pruebas pasando.
4. Si falla una prueba, no avanzar de fase.
5. Todo cambio de esquema debe pasar por Alembic.
6. Registrar decisiones y errores en bitacora por fase.
7. Hacer cambios pequenos e incrementales (commits pequenos).

---

## 6) Flujo estandar que debe cumplir CADA fase
1. Analizar codigo actual del area de la fase.
2. Implementar cambios minimos necesarios.
3. Ejecutar pruebas unitarias relacionadas.
4. Ejecutar smoke tests manuales de UI/API.
5. Corregir errores detectados.
6. Documentar resultado de fase.
7. Cerrar solo si cumple DoD (Definition of Done).

Gate de paso obligatorio:
- Si hay 1 error critico pendiente -> fase NO aprobada.

---

## 7) Definicion de datos objetivo (escalable)
### 7.1 Nuevas entidades recomendadas
1. `plantillas_horario`
- id
- aula_id
- grupo
- periodo
- turno
- version
- activo
- created_at, updated_at

2. `plantilla_bloques`
- id
- plantilla_id
- dia_semana (1..6)
- hora_inicio (HH:MM)
- hora_fin (HH:MM)
- tipo_bloque (CLASE|RECREO|LIBRE)
- etiqueta (opcional)
- orden_visual (opcional)
- activo
- created_at, updated_at

3. Extender `horarios` (tabla actual)
- `plantilla_bloque_id` nullable (FK a `plantilla_bloques.id`)
- Mantener campos actuales para compatibilidad.

### 7.2 Reglas de negocio clave
1. `hora_inicio < hora_fin` siempre.
2. No puede haber solapamiento de bloques en una plantilla (mismo dia).
3. Un bloque RECREO o LIBRE no debe tener curso/docente asignado.
4. Asignacion de clase en bloque CLASE valida conflicto de:
- grupo
- docente
- aula
5. Duracion minima configurable (recomendado: 15 min).

---

## 8) Plan fase por fase

## FASE 0 - Preparacion, baseline y seguridad
### Objetivo
Dejar una linea base medible y segura antes de tocar arquitectura.

### Tareas
1. Crear rama de trabajo dedicada.
2. Correr pruebas actuales backend.
3. Levantar backend y desktop para smoke baseline.
4. Documentar comportamiento actual de horarios (capturas y casos).

### Verificaciones
1. `backend/tests` ejecuta sin errores nuevos.
2. Crear y eliminar un bloque actual sigue funcionando.

### Entregables
1. Bitacora fase 0.
2. Baseline de pruebas y comportamiento.

### DoD Fase 0
- Baseline documentado y reproducible.

---

## FASE 1 - Modelo de datos y migraciones
### Objetivo
Crear soporte estructural para plantillas sin romper lo existente.

### Tareas
1. Crear modelos SQLAlchemy: `PlantillaHorario`, `PlantillaBloque`.
2. Agregar FK opcional `plantilla_bloque_id` a `Horario`.
3. Crear migracion Alembic con indices utiles:
- (plantilla_id, dia_semana, hora_inicio)
- (aula_id, grupo, periodo, turno, activo)
4. Crear constraints/checks basicos de horas y tipo_bloque.

### Verificaciones
1. `alembic upgrade head` funciona en limpio.
2. Insert de bloque valido funciona.
3. Insert con hora fin <= inicio falla correctamente.

### Entregables
1. Modelos nuevos.
2. Migracion alembic.
3. Tests de modelo/servicio basico.

### DoD Fase 1
- Esquema listo, migracion reversible, sin regresion en CRUD actual.

---

## FASE 2 - API y servicios de plantilla
### Objetivo
Exponer API robusta para CRUD de plantillas y bloques.

### Tareas
1. Crear schemas pydantic para plantilla y bloque.
2. Crear `plantilla_horario_service.py`.
3. Crear rutas nuevas (ejemplo):
- `GET /plantillas-horario/`
- `POST /plantillas-horario/`
- `PUT /plantillas-horario/{id}`
- `DELETE /plantillas-horario/{id}`
- `GET /plantillas-horario/{id}/bloques`
- `POST /plantillas-horario/{id}/bloques`
- `PUT /plantilla-bloques/{id}`
- `DELETE /plantilla-bloques/{id}`
- `POST /plantillas-horario/{id}/bloques/batch-upsert`
4. Implementar validaciones anti-solape por dia.
5. Agregar endpoint para obtener grilla final por aula+grupo+periodo+turno.

### Verificaciones
1. Tests de API para casos felices y casos invalidos.
2. Respuestas de error claras (400/422) en conflictos.

### Entregables
1. Servicios y rutas nuevas.
2. Tests backend fase 2.

### DoD Fase 2
- API de plantillas operativa y validada.

---

## FASE 3 - Integracion con modulo de horarios existente
### Objetivo
Conectar `horarios` con bloques de plantilla sin romper uso actual.

### Tareas
1. Extender servicio actual de horarios para aceptar `plantilla_bloque_id`.
2. Validar que asignacion solo aplique a bloque tipo CLASE.
3. Mantener endpoint actual de horarios con compatibilidad.
4. Ajustar `obtener_horario_aula` para consumir estructura dinamica.

### Verificaciones
1. Crear horario con `plantilla_bloque_id` valido.
2. Rechazar asignacion sobre RECREO/LIBRE.
3. Flujos antiguos siguen funcionando temporalmente.

### Entregables
1. Compatibilidad dual (viejo + nuevo).
2. Tests de integracion horarios + plantilla.

### DoD Fase 3
- Integracion lista sin regresiones criticas.

---

## FASE 4 - Desktop UI: eliminar rigidez de slots
### Objetivo
Hacer que la vista de horarios renderice bloques reales (no fijos).

### Tareas
1. En `horarios_view.py` quitar dependencia de slots hardcodeados.
2. Renderizar filas por bloques devueltos por API.
3. Mostrar tipo de bloque (CLASE/RECREO/LIBRE) visualmente.
4. En `dialogo_horario.py`, permitir crear bloque personalizado:
- dia
- hora inicio
- hora fin
- tipo bloque
5. Crear dialogo simple de gestion de plantilla por dia.
6. Permitir multiples recreos por dia.
7. Permitir dias con una sola clase.

### Verificaciones
1. Caso A: lunes con 1 bloque de clase.
2. Caso B: martes con 2 recreos.
3. Caso C: miercoles con duraciones distintas.
4. No crash de UI al refrescar o cambiar aula/grupo.

### Entregables
1. Vista desktop dinamica.
2. Dialogos de gestion funcionales.
3. Smoke test UI documentado.

### DoD Fase 4
- Usuario puede personalizar horas y recreos sin tocar codigo.

---

## FASE 5 - Migracion de datos y backfill
### Objetivo
Llevar datos actuales al nuevo modelo de plantilla sin perder informacion.

### Tareas
1. Script de backfill: crear plantilla por aula/grupo/periodo/turno.
2. Mapear horarios existentes a `plantilla_bloque_id`.
3. Generar reporte de registros no mapeados.
4. Ejecutar backfill en entorno de prueba primero.

### Verificaciones
1. Conteo antes/despues consistente.
2. Muestra aleatoria de 30 registros validada.
3. Ningun horario activo sin correspondencia injustificada.

### Entregables
1. Script de backfill idempotente.
2. Reporte de migracion.

### DoD Fase 5
- Datos historicos utilizables bajo nuevo modelo.

---

## FASE 6 - Calidad, rendimiento y observabilidad
### Objetivo
Asegurar estabilidad operativa y rendimiento bajo carga.

### Tareas
1. Agregar pruebas de regresion del modulo horario.
2. Medir latencia de endpoints nuevos (p50/p95).
3. Agregar logs estructurados para operaciones de plantilla.
4. Verificar indices con EXPLAIN en consultas clave.

### Verificaciones
1. p95 estable segun baseline objetivo.
2. Sin errores 5xx en flujos principales.
3. Trazabilidad de errores por request_id.

### Entregables
1. Reporte tecnico de calidad/performance.
2. Lista de ajustes post tuning.

### DoD Fase 6
- Sistema listo para despliegue controlado.

---

## FASE 7 - Rollout gradual y cierre
### Objetivo
Activar funcionalidad nueva con bajo riesgo.

### Tareas
1. Activar feature flag por modulo o por sede.
2. Monitorear errores y feedback inicial.
3. Tener rollback operativo documentado.
4. Cerrar deuda de compatibilidad legacy.

### Verificaciones
1. Sin incidentes criticos durante ventana piloto.
2. KPIs operativos dentro de rango esperado.

### Entregables
1. Acta de despliegue.
2. Plan de mejoras fase 2 UX (drag and drop opcional).

### DoD Fase 7
- Funcionalidad en produccion estable y mantenible.

---

## 9) Matriz de riesgos y mitigaciones
1. Riesgo: romper flujo actual de horarios.
- Mitigacion: compatibilidad dual + feature flag.

2. Riesgo: datos inconsistentes en migracion.
- Mitigacion: backfill idempotente + reporte de no mapeados.

3. Riesgo: UI inestable por asincronia.
- Mitigacion: tokens separados por flujo de carga y pruebas de refresco.

4. Riesgo: conflictos horarios no detectados.
- Mitigacion: validacion backend obligatoria y tests de superposicion.

---

## 10) Prompt maestro para ejecutar TODO el plan con IA
Usar este prompt con la IA ejecutora:

"""
Eres un ingeniero senior de Python/FastAPI/CustomTkinter.
Necesitas implementar el plan por fases del archivo docs/PLAN_FASEADO_HORARIOS_ESCALABLE_IA.md.

Reglas:
1) No saltes fases.
2) Al finalizar cada fase: ejecutar pruebas, corregir errores, documentar bitacora y pedir confirmacion para avanzar.
3) No romper endpoints existentes sin compatibilidad temporal.
4) Todo cambio de DB via Alembic.
5) Si hay un error, detener avance, mostrar causa raiz y proponer fix minimo.

Salida obligatoria por fase:
- Cambios realizados
- Archivos tocados
- Pruebas ejecutadas y resultado
- Errores encontrados y solucion
- Riesgos abiertos
- Estado de fase: APROBADA / NO APROBADA
"""

---

## 11) Prompt por fase (plantilla reutilizable)
Copiar y reemplazar N por el numero de fase.

"""
Ejecuta SOLO la FASE N del archivo docs/PLAN_FASEADO_HORARIOS_ESCALABLE_IA.md.

Instrucciones:
1) Lee objetivo, tareas, verificaciones y DoD de la fase N.
2) Implementa cambios minimos necesarios.
3) Ejecuta pruebas relacionadas.
4) Si hay errores, corrige antes de cerrar fase.
5) No avances a la fase N+1.

Formato de respuesta:
1. Resumen tecnico
2. Archivos modificados
3. Validaciones ejecutadas
4. Errores detectados y correcciones
5. Checklist DoD (cumple/no cumple)
6. Estado final: APROBADA / NO APROBADA
"""

---

## 12) Comandos sugeridos de validacion (Windows PowerShell)
### Backend
1. Instalar deps:
- `cd backend`
- `.venv\Scripts\Activate.ps1`
- `pip install -r requirements.txt`

2. Migraciones:
- `alembic upgrade head`

3. Pruebas:
- `pytest -q`
- `pytest tests/test_health.py -q`
- `pytest tests/test_alumnos_periodos.py -q`

4. Levantar API:
- `python -m uvicorn main:app --reload`

### Desktop
1. Activar entorno:
- `cd desktop`
- `.venv\Scripts\Activate.ps1`

2. Smoke manual:
- `python main.py`

---

## 13) Checklist de cierre final (calidad total)
1. No hay hardcode de slots en UI.
2. Se permiten horas personalizadas por dia.
3. Se permiten multiples recreos por dia.
4. Se permite dia con una sola hora de clase.
5. Backend rechaza solapamientos invalidos.
6. Pruebas backend y smoke desktop aprobadas.
7. Migraciones y rollback documentados.
8. Bitacora final completada.

---

## 14) Recomendacion final de ejecucion
Para minimizar errores:
1. Ejecutar 1 fase por dia o por bloque corto.
2. Cerrar cada fase con pruebas antes de continuar.
3. No mezclar refactors de estilo con cambios funcionales.
4. Usar commits pequenos por sub-tarea.
5. Mantener siempre una ruta clara de rollback.

Si se sigue este plan, el modulo de horarios quedara personalizable, robusto y preparado para escalar.
