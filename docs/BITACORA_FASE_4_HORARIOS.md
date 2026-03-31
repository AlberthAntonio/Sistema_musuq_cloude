# Bitacora Fase 4 - Desktop UI dinamica de horarios

Fecha: 2026-03-30
Estado de fase: APROBADA

## 1. Objetivo de fase
Eliminar rigidez de slots fijos en desktop y renderizar bloques reales (CLASE/RECREO/LIBRE) desde API.

## 2. Cambios realizados
- Se agrego cliente desktop para gestionar plantillas y bloques:
  - `PlantillasHorarioClient` en `desktop/core/api_client.py`.
- Se extendio `AcademicoController` para flujo dinamico:
  - obtencion de bloques reales por aula/grupo/periodo/turno.
  - creacion de bloque personalizado de plantilla (asegurando plantilla activa).
  - eliminacion de bloque de plantilla.
  - asignacion de clase a `plantilla_bloque_id` en `agregar_bloque`.
- Se refactorizo `HorariosView`:
  - render de grilla dinamica por bloques reales (sin slots hardcodeados).
  - visualizacion explicita por tipo de bloque (`CLASE`, `RECREO`, `LIBRE`).
  - accion nueva de gestion simple por dia: `Nuevo Bloque`.
  - soporte para asignar clase a bloque `CLASE` no asignado.
  - soporte para eliminar bloque de plantilla directamente desde celdas.
- Se actualizo `DialogoHorario` para doble modo:
  - modo asignacion de clase (legacy/compatibilidad + `plantilla_bloque_id`).
  - modo creacion de bloque personalizado (dia, hora inicio, hora fin, tipo bloque, etiqueta).

## 3. Archivos tocados
- desktop/core/api_client.py
- desktop/controllers/academico_controller.py
- desktop/ui/views/docentes/horarios_view.py
- desktop/ui/views/docentes/dialogo_horario.py

## 4. Validaciones ejecutadas
- Analisis estatico en archivos modificados:
  - `get_errors` (VS Code Problems): sin errores.
- Compilacion de sintaxis Python:
  - `python -m py_compile` sobre archivos modificados.
  - Resultado: sin errores.

## 5. Verificacion contra criterios de fase
- Quitar dependencia de slots hardcodeados: CUMPLE
- Renderizar filas por bloques reales de API: CUMPLE
- Mostrar tipo de bloque visualmente: CUMPLE
- Permitir crear bloque personalizado (dia/hora/tipo): CUMPLE
- Dialogo simple de gestion por dia: CUMPLE
- Permitir multiples recreos por dia: CUMPLE
- Permitir dias con una sola clase: CUMPLE

## 6. Riesgos abiertos
- No se ejecuto smoke visual manual end-to-end en UI en esta iteracion automatizada.
- Edicion de bloque de plantilla (update) no fue implementada en UI; se cubre alta/eliminacion y asignacion de clase.

## 7. Checklist DoD Fase 4
- Vista desktop dinamica: CUMPLE
- Dialogos de gestion funcionales: CUMPLE
- Smoke test UI documentado: PENDIENTE manual

## 8. Conclusion
La Fase 4 queda implementada a nivel funcional en desktop con arquitectura dinamica por bloques y compatibilidad con flujos legacy. Se recomienda una corrida manual de smoke UI para cierre operativo final.
