# Runbook de Operaciones Base (Producción)

## Introducción al Backend Refactorizado
Este documento describe cómo lidiar con las operaciones del `Backend` del Sistema Musuq de su nueva naturaleza resistente (Escalabilidad Fase 4) 

Ubicación del Backend: `d:\Asistencia program\Asistencia_Personal\implementacion cloude\Sistema_Musuq_Cloude\backend`

---

## 🔧 Rutinas Diarias de Administración

### Levantar el Servidor en Producción
```bash
# Cambiar al directorio
cd backend/

# Arrancar Uvicorn en producción (Sin --reload)
.venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```
> [!TIP]
> **Workers recomendados**: Según el hardware que adquieran. Una regla general es `workers = (Núcleos del CPU * 2) + 1`.


### Actualizar Base de Datos (Si hay cambios de Modelos)
Si un programador añade campos nuevos (por ejemplo "código de descuento") e instruye un nuevo Release, tienes que ejecutar Alembic para actualizar los esquemas:
```bash
.venv\Scripts\alembic upgrade head
```

### Operacion de Rollout Horarios (Fase 7)
El modulo de horarios dinamicos por plantilla puede habilitarse de forma gradual por aula.

Variables de entorno relevantes:
- `HORARIOS_PLANTILLAS_ENABLED=true|false`
- `HORARIOS_PLANTILLAS_ALLOW_AULAS=*` o CSV de IDs (ejemplo: `1,2,5`)

Procedimiento recomendado:
```bash
# 1) Canary: habilitar solo aulas piloto
HORARIOS_PLANTILLAS_ENABLED=true
HORARIOS_PLANTILLAS_ALLOW_AULAS=1,2

# 2) Reiniciar backend
.venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# 3) Monitorear KPIs y headers de modo
.venv\Scripts\python -m scripts.monitor_horarios_rollout_fase7
```

Verificacion funcional en respuesta de `GET /aulas/{id}/horarios`:
- `X-Horarios-Mode: dynamic|legacy`
- `X-Horarios-Rollout-Reason: <motivo de decision>`

Rollback rapido:
```bash
HORARIOS_PLANTILLAS_ENABLED=false
# Reiniciar backend
```
Con ese ajuste, todo el modulo vuelve a modo `legacy` sin revertir esquema.

---

## 🩺 Control de Crisis (Troubleshooting)

### Caso 1: La Interfaz Desktop muestra "Status 422" 
**Causa:** El limitador anti-ataques protegió el servidor por una exigencia descabellada desde la vista del Escritorio.
**Diagnóstico:**
- Revisa la Terminal de Uvicorn (o tu archivo `.log` físico usando el `X-Request-Id` si estás en Cloud).
- Corrobora si un usuario está usando una versión antigua de `desktop/core/api_client.py` que no contaba con "Patrón Adapter Paginado". El Backend ahora restringe `MAX_PAGE_SIZE = 200` y si Desktop dice `10,000`, tu nuevo `APIClient` lo fracciona de a `200` transparente. 
**Subterfugio Temporal:** En emergencias absolutas, altera `MAX_PAGE_SIZE = 5000` en `backend/app/core/config.py` y reinicia el servidor.

### Caso 2: Sistema Musuq "Lento" al intentar crear un pago
**Causa:** Retraso DB / Indexing.
**Solución:** Los índices se han agregado en Fase 2. Monitorea los Logs JSON para localizar demoras. E.g:
`{"path": "/pagos/", "status": 201, "duration": "1402.5ms"}` -> Reportar tiempo demorado en la tabla de Pagos con el log ID.


### Caso 3: "Error 500: Database lock" en picos de Matrícula (Marzo)
**Causa:** Cien cajeros anotando pagos en el mismo milisegundo en SQLite (`musuq.db`).
**Solución a largo plazo:** El Backend ya soporta PostgreSQL mediante Repositorios abstractos y SQLAlchemy. Compra una Base de Datos AWS Postgres, cámbiala en tu `.env` (`USE_SQLITE=False` y coloca el string `DATABASE_URL`) y reinicia. Cero líneas de código alteradas.
