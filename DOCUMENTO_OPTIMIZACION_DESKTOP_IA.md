# Documento Maestro de Optimizacion Desktop para IA

## 1) Proposito
Este documento define el plan tecnico y operativo para optimizar la app desktop (CustomTkinter) con foco en:
- navegacion fluida entre modulos
- reduccion de bloqueos del hilo UI
- menor latencia percibida al cambiar vistas
- estabilidad y ausencia de errores regresivos

Este documento esta pensado para ser entregado a una IA ejecutora de cambios en codigo.

---

## 2) Alcance
Incluir:
- modulo de navegacion principal
- vistas pesadas de pagos, docentes, cursos y asistencia
- controladores que hoy hacen cargas sincronas
- instrumentacion de rendimiento
- plan de pruebas y criterios de aceptacion

No incluir (por ahora):
- rediseño visual completo
- migracion a web
- reescritura de backend

---

## 3) Estado actual y hallazgos tecnicos

### 3.1 Navegacion y cache de vistas
La app cachea vistas, pero al cambiar de pantalla solo hace ocultamiento visual, no ciclo de vida completo.
Referencia:
- desktop/ui/main_window.py:305
- desktop/ui/main_window.py:308

Impacto:
- vistas con timers o tareas periodicas pueden seguir activas en segundo plano
- consumo extra de CPU y micro-lag acumulado

### 3.2 Cargas sincronas en hilo UI
Hay pantallas que disparan busquedas/cargas directas al entrar o al interactuar, bloqueando UI.
Referencias criticas:
- desktop/ui/views/pagos/caja_view.py:35
- desktop/ui/views/pagos/caja_view.py:528
- desktop/ui/views/pagos/caja_view.py:612
- desktop/ui/views/pagos/estado_cuenta_view.py:34
- desktop/ui/views/pagos/estado_cuenta_view.py:419
- desktop/ui/views/pagos/estado_cuenta_view.py:495
- desktop/ui/views/docentes/gestion_docentes_view.py:325
- desktop/ui/views/docentes/gestion_docentes_view.py:466
- desktop/ui/views/docentes/cursos_view.py:34
- desktop/ui/views/docentes/cursos_view.py:35

### 3.3 Llamadas encadenadas y costo de red
En cursos/docentes hay varias llamadas al backend por flujo de pantalla.
Referencias de controladores:
- desktop/controllers/academico_controller.py:24
- desktop/controllers/academico_controller.py:26
- desktop/controllers/academico_controller.py:56
- desktop/controllers/academico_controller.py:58
- desktop/controllers/docentes_controller.py:15
- desktop/controllers/docentes_controller.py:17

### 3.4 Timers recurrentes activos
Asistencia mantiene tareas periodicas y puede impactar navegacion si no se suspenden al ocultar vista.
Referencias:
- desktop/ui/views/asistencia/asistencia_view.py:378
- desktop/ui/views/asistencia/asistencia_view.py:394
- desktop/ui/views/asistencia/asistencia_view.py:498

### 3.5 Logging de debug en runtime
Hay prints de debug en capa API que agregan ruido y costo de IO.
Referencias:
- desktop/core/api_client.py:224
- desktop/core/api_client.py:226
- desktop/core/api_client.py:231

---

## 4) Objetivos de rendimiento (SLO)

### 4.1 Metas de UX
- Navegacion entre vistas ya cacheadas: <= 120 ms (p95)
- Primera apertura de vista: <= 400 ms para primer paint de layout
- Sin congelamiento perceptible en UI durante cargas
- Busqueda con debounce: respuesta visual <= 150 ms (sin contar red)

### 4.2 Metas tecnicas
- 0 llamadas HTTP bloqueantes en hilo UI
- 100% de vistas con contrato de ciclo de vida (on_show/on_hide)
- timers cancelables y cancelados al ocultar vista
- reduccion de CPU en idle tras navegar 20 cambios de modulo

---

## 5) Reglas de implementacion para la IA

1. No romper APIs publicas existentes salvo necesidad justificada.
2. Mantener compatibilidad funcional de cada modulo.
3. Todo acceso de red debe salir del hilo principal.
4. Toda actualizacion visual desde background debe entrar por after(0, ...).
5. Implementar control de solicitudes obsoletas (request token/version).
6. Evitar recreacion masiva de widgets si puede hacerse diff/update.
7. Eliminar logs debug ruidosos o llevarlos a logger con nivel.
8. Agregar protecciones de carrera y de widgets destruidos.

---

## 6) Plan por fases

## Fase 1: Instrumentacion y baseline
Objetivo: medir antes de tocar.

Tareas:
1. Crear util de medicion de tiempos por vista:
   - tiempo import de vista
   - tiempo create_widgets
   - tiempo primer paint
   - tiempo carga datos
2. Integrar medicion en main_window al cambiar vista.
3. Registrar p50/p95 por modulo en memoria y salida controlada.

Entregables:
- reporte baseline por modulo
- ranking de pantallas mas lentas

## Fase 2: Ciclo de vida de vistas
Objetivo: evitar trabajo fantasma en background.

Tareas:
1. Definir contrato opcional en vistas:
   - on_show()
   - on_hide()
   - cleanup()
2. En main_window:
   - antes de ocultar vista actual, llamar on_hide si existe
   - al mostrar nueva vista, llamar on_show si existe
3. Asegurar que vistas con timers los cancelen en on_hide/cleanup.

Entregables:
- main_window con ciclo de vida
- asistencia con timers controlados

## Fase 3: Carga no bloqueante por modulo critico
Objetivo: eliminar freeze de navegacion.

Tareas minimas por modulo:
1. Pagos/caja_view:
   - mover busqueda y carga de estado de cuenta a thread
   - mostrar skeleton/loading inmediato
   - usar request_id para ignorar respuestas viejas
2. Pagos/estado_cuenta_view:
   - misma estrategia de background + request_id
3. Docentes/gestion_docentes_view:
   - cargar_tabla en background
   - debounce para busqueda por teclado
4. Docentes/cursos_view:
   - cargar catalogo y mallas en background
   - evitar n llamadas redundantes para pestaña TODOS

Entregables:
- pantallas criticas sin llamadas sync en UI

## Fase 4: Cache y batching de UI
Objetivo: reducir costo total de render.

Tareas:
1. Cache TTL (30-60 s) para catalogos frecuentes.
2. Render por lotes para listas largas (chunk de 25/50).
3. Reutilizar widgets cuando sea viable.
4. Evitar destroy masivo si se puede actualizar contenido.

Entregables:
- scroll y filtros mas suaves
- menor consumo CPU en interaccion

## Fase 5: Endurecimiento y QA
Objetivo: estabilidad y cero regresiones graves.

Tareas:
1. Probar 20 cambios de modulo seguidos.
2. Probar busquedas rapidas en modulos pesados.
3. Probar backend lento/sin red (timeouts y mensajes).
4. Validar que no queden timers vivos al salir de vista.

Entregables:
- checklist QA completo
- comparativo before/after

---

## 7) Cambios concretos por archivo (guia)

### 7.1 desktop/ui/main_window.py
Implementar:
- invocacion segura de on_hide para vista actual
- invocacion segura de on_show para vista nueva
- medicion de tiempo de show_view

Criterio:
- no romper cache existente

### 7.2 desktop/ui/views/asistencia/asistencia_view.py
Implementar:
- metodo on_hide que cancele after ids activos
- limpiar debounce y timers recurrentes
- evitar relanzar timers si vista no esta visible

### 7.3 desktop/ui/views/pagos/caja_view.py
Implementar:
- _ejecutar_busqueda en background
- actualizar_estado_cuenta en background
- request_id monotono para descartar respuestas viejas
- loading states no bloqueantes

### 7.4 desktop/ui/views/pagos/estado_cuenta_view.py
Implementar lo mismo que caja_view.

### 7.5 desktop/ui/views/docentes/gestion_docentes_view.py
Implementar:
- cargar_tabla en hilo background
- UI update via after
- debounce de busqueda

### 7.6 desktop/ui/views/docentes/cursos_view.py
Implementar:
- carga inicial asincrona de catalogo y mallas
- cache local para evitar recargas redundantes
- consolidado TODOS desde cache, no roundtrips innecesarios

### 7.7 desktop/core/api_client.py
Implementar:
- eliminar prints debug de buscar
- usar logger configurable por nivel

---

## 8) Criterios de aceptacion

Se considera exitoso si:
1. Navegar entre 8 modulos distintos no produce cuelgues.
2. Primera apertura de modulo muestra estructura en menos de 400 ms.
3. No hay stutter al escribir en buscadores criticos.
4. Timers de Asistencia se detienen al salir de vista.
5. No aparecen errores de thread/UI en consola.
6. Comparativo before/after muestra mejora de p95 >= 35% en modulos criticos.

---

## 9) Plan de pruebas

### 9.1 Pruebas funcionales
- abrir cada modulo principal
- ejecutar busqueda
- seleccionar item
- volver a dashboard
- repetir x20

### 9.2 Pruebas de rendimiento
- medir latencia cambio vista
- medir tiempo primer paint
- medir tiempo carga datos
- medir CPU en idle despues de stress

### 9.3 Pruebas de resiliencia
- backend lento
- backend no disponible
- token expirado
- respuestas vacias

---

## 10) Riesgos y mitigacion

1. Race conditions en respuestas asincronas
   - Mitigar con request_id y guardas de vigencia
2. UI update en widget destruido
   - Mitigar con winfo_exists y cancelaciones
3. Datos stale por cache
   - Mitigar con TTL corto + refresh manual
4. Regresiones de comportamiento
   - Mitigar con smoke tests por modulo

---

## 11) Orden recomendado de ejecucion

1. main_window lifecycle + instrumentacion
2. asistencia timers cleanup
3. pagos caja
4. pagos estado de cuenta
5. gestion docentes
6. cursos
7. limpieza de logs debug y hardening

---

## 12) Prompt listo para otra IA (copiar y pegar)

Objetivo:
Optimiza rendimiento y fluidez de navegacion en app desktop CustomTkinter sin romper funcionalidad.

Contexto tecnico:
- Proyecto: Sistema Musuq Cloude (desktop)
- Navegacion actual cachea vistas pero solo usa pack_forget
- Existen cargas sincronas en hilo UI en pagos/docentes/cursos
- Asistencia usa timers recurrentes

Requisitos obligatorios:
1. Implementar ciclo de vida de vistas (on_show, on_hide, cleanup) invocado desde main_window.
2. Mover todas las llamadas de red de vistas criticas a background thread.
3. Todas las actualizaciones de UI deben entrar por after(0, ...).
4. Implementar request_id para descartar respuestas obsoletas.
5. Cancelar timers/after al ocultar vistas.
6. Eliminar prints debug de API y usar logger por nivel.
7. Mantener comportamiento funcional actual.

Archivos prioritarios:
- desktop/ui/main_window.py
- desktop/ui/views/asistencia/asistencia_view.py
- desktop/ui/views/pagos/caja_view.py
- desktop/ui/views/pagos/estado_cuenta_view.py
- desktop/ui/views/docentes/gestion_docentes_view.py
- desktop/ui/views/docentes/cursos_view.py
- desktop/core/api_client.py

Criterios de aceptacion:
- Navegacion suave sin freeze perceptible
- Primera apertura con layout visible rapido
- Sin excepciones de thread/UI
- Mejora medible de tiempos p95

Forma de entrega:
1. lista de archivos modificados
2. resumen de decisiones tecnicas
3. metricas before/after
4. riesgos residuales y siguientes pasos

---

## 13) Nota final para ejecucion
Si durante la implementacion aparece un cambio no compatible, priorizar:
1) estabilidad de UI
2) no bloqueo del hilo principal
3) mantener funcionalidad existente

Fin del documento.
