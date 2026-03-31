# Plan de Mejoras UX - Fase 2 Horarios (post rollout)

Fecha: 2026-03-30
Objetivo: Elevar productividad del operador academico tras estabilizar rollout de horarios dinamicos.

## 1. Objetivos UX
1. Reducir tiempo de armado de plantilla por aula.
2. Minimizar errores de edicion en bloques.
3. Mejorar visibilidad de conflictos de asignacion.

## 2. Mejoras priorizadas

### 2.1 Drag and drop opcional para bloques
- Reordenar bloques por dia sin editar manualmente horas.
- Ajustar automaticamente `orden_visual`.

### 2.2 Edicion rapida en grilla
- Acciones inline: duplicar bloque, mover a otro dia, convertir tipo (CLASE/RECREO/LIBRE).
- Confirmacion corta para operaciones destructivas.

### 2.3 Presets de jornada
- Plantillas predefinidas por modalidad (COLEGIO/ACADEMIA).
- Carga inicial con 1 click y posterior personalizacion.

### 2.4 Validacion visual temprana
- Resaltar solapamientos antes de guardar.
- Etiquetas de color por tipo de bloque.

### 2.5 Accesibilidad y feedback
- Navegacion por teclado en editor de bloques.
- Mensajes de exito/error consistentes con trazabilidad por request_id.

## 3. Metricas de exito
1. Tiempo medio de configuracion de horario por aula: reducir al menos 30%.
2. Tasa de errores por solapamiento en edicion: reducir al menos 50%.
3. Satisfaccion de usuario administrativo en piloto UX: >= 4/5.

## 4. Plan de ejecucion sugerido
1. Sprint 1: wireframes + validacion con usuarios clave.
2. Sprint 2: drag and drop + edicion inline.
3. Sprint 3: presets + validacion visual + ajustes de accesibilidad.
4. Sprint 4: hardening, pruebas E2E y despliegue gradual UI.

## 5. Dependencias
1. Mantener endpoints de plantilla estables (Fases 2-7 ya cerradas).
2. Definir contrato de eventos UI para sincronizacion de grilla.
3. Alinear diseño con restricciones de rendimiento desktop.

## 6. Criterio de salida
- Operadores completan escenarios A/B/C del plan sin asistencia tecnica.
- Sin regresiones funcionales en CRUD de horarios.
- Pruebas de humo desktop aprobadas en aulas piloto.
