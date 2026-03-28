# PENDIENTES Y ERRORES — Sistema Musuq Cloud
> Última revisión: 12 de marzo de 2026
> Marcar con [x] cuando esté resuelto, [ ] cuando esté pendiente.
> Cada ítem está redactado como instrucción directa para la IA: copia y pega el bloque completo.

---

## 🔴 CATEGORÍA 1 — CRASHES GARANTIZADOS

---

### [ ] CRASH 1 — Crear vista "Resumen Docentes" que no existe

**INSTRUCCIÓN PARA LA IA:**
Lee el archivo `desktop/ui/views/docentes/gestion_docentes_view.py` para entender el estilo visual y el patrón de la sección de docentes. Luego crea el archivo `desktop/ui/views/docentes/resumen_docentes_view.py` con una clase `ResumenDocentePanel(CTkFrame)` que muestre un resumen básico de docentes (tabla con nombre, especialidad, cursos asignados). La clase debe recibir `parent` y `auth_client` en su `__init__`, instanciar `DocentesController(auth_client.token)` y cargar los datos con `obtener_docentes()`. No modifiques ningún otro archivo.

---

### [ ] CRASH 2 — Corregir import incorrecto en `main_window.py` para Constancias

**INSTRUCCIÓN PARA LA IA:**
Abre únicamente `desktop/ui/main_window.py`. Busca el método `show_academico_constancias`. Dentro de ese método hay una línea que empieza con `from desktop.ui.views.academico.doc_constancias import`. Cámbiala a `from ui.views.academico.doc_constancias import ConstanciasView`. No modifiques ninguna otra línea ni ningún otro archivo.

---

### [ ] CRASH 3 — Corregir import con alias incorrecto en `doc_constancias.py`

**INSTRUCCIÓN PARA LA IA:**
Abre únicamente `desktop/ui/views/academico/doc_constancias.py`. Busca la línea que dice `from core.theme_manager import TM`. Cámbiala a `from core.theme_manager import ThemeManager as TM`. No modifiques ninguna otra línea ni ningún otro archivo.

---

### [ ] CRASH 4 — Corregir parámetro inválido en `CarnetController.generar_carnets_pdf()`

**INSTRUCCIÓN PARA LA IA:**
Abre únicamente `desktop/controllers/carnet_controller.py`. Busca la llamada a `landscape(card_size=...)`. Cámbiala para que `landscape()` reciba la tupla directamente como argumento posicional sin el kwarg `card_size`. Ejemplo: `landscape(card_size=(85.6 * mm, 53.98 * mm))` → `landscape((85.6 * mm, 53.98 * mm))`. No modifiques ninguna otra línea ni ningún otro archivo.

---

## 🟠 CATEGORÍA 2 — FUNCIONES SIN IMPLEMENTAR

---

### [ ] SIN IMPL. 1 — Conectar vista de Periodos Lectivos a la API real

**INSTRUCCIÓN PARA LA IA:**
Lee estos dos archivos completos antes de hacer cambios: `desktop/ui/views/config/config_periodo_lectivo.py` y `desktop/core/api_client.py` (busca la clase `PeriodosClient`). Luego modifica `config_periodo_lectivo.py` para que:
1. En `__init__` instancie `PeriodosClient(token)` recibiendo `auth_client` como parámetro (igual que otras vistas).
2. Reemplaza el método `cargar_periodos_dummy()` por uno real que llame a `GET /periodos/` y pueble la tabla con los datos reales.
3. El botón "Nuevo periodo" debe llamar a `POST /periodos/` con los datos del formulario.
4. El botón "Cerrar periodo" (si existe) debe llamar a `POST /periodos/{id}/cerrar`.
No modifiques ningún otro archivo. No inventes campos que no existen en el schema `PeriodoCreate` (campos válidos: `nombre`, `tipo`, `fecha_inicio`, `fecha_fin`, `estado`).

---

### [ ] SIN IMPL. 2 — Configuración de institución: conectar al backend

**⚠️ REQUIERE DECISIÓN DEL DESARROLLADOR — NO COPIAR AÚN**
Requiere definir qué campos de institución se quieren guardar y crear un endpoint en el backend.
Cuando lo tengas definido, reescribe esta instrucción con los campos concretos.

**ESTADO:** Pendiente de definición de requisitos.

---

### [ ] SIN IMPL. 3 — Integración SMS/WhatsApp

**⚠️ REQUIERE DECISIÓN EXTERNA — NO COPIAR AÚN**
Requiere elegir proveedor (Twilio, etc.) y tener credenciales. No implementable sin esa información.

**ESTADO:** Pendiente de decisión de proveedor.

---

### [ ] SIN IMPL. 4 — Boletas de notas: reemplazar datos aleatorios por datos reales de la BD

**INSTRUCCIÓN PARA LA IA:**
Lee estos archivos completos antes de hacer cambios: `desktop/controllers/academico_controller.py` y `desktop/core/api_client.py` (busca las clases `NotasClient` y `SesionesClient`). Luego modifica únicamente `desktop/controllers/academico_controller.py`:
1. Localiza el método `obtener_data_boleta(self, alumno_id)`.
2. Reemplaza completamente su implementación para que llame a `GET /sesiones/?limit=100` y `GET /notas/?alumno_id={alumno_id}&limit=500`, y construya el mismo formato de diccionario que retorna el mock pero con datos reales.
3. NO uses `random`, NO dejes datos hardcodeados de notas.
4. Si la API retorna error, retorna `None` y loguea el error con `self._log_operacion`.
No modifiques ningún otro archivo.

---

### [ ] SIN IMPL. 5 — Crear vista de Historial de Alumno

**INSTRUCCIÓN PARA LA IA:**
Lee los archivos `desktop/ui/views/alumnos/alumnos_list_view.py` y `desktop/core/api_client.py` (clases `AlumnoClient`, `AsistenciaClient`) para entender el patrón visual. Luego:
1. Crea `desktop/ui/views/alumnos/historial_alumno_view.py` con clase `HistorialAlumnoPanel(CTkFrame)` que reciba `parent` y `auth_client`.
2. La vista debe tener: buscador de alumno por nombre/DNI (`GET /alumnos/buscar?q=`) y al seleccionar uno mostrar su historial de asistencias (`GET /asistencia/?alumno_id={id}&limit=200`) en tabla con columnas: Fecha, Estado, Turno, Observación.
3. Abre `desktop/ui/main_window.py` y crea el método `show_alumnos_historial` que cargue `HistorialAlumnoPanel`. Luego en el submenú de Alumnos cambia `"Historial": self.show_alumnos_nuevo` por `"Historial": self.show_alumnos_historial`.
No modifiques nada más.

---

### [ ] SIN IMPL. 6 — Implementar generación de PDF en Estado de Cuenta

**INSTRUCCIÓN PARA LA IA:**
Lee estos archivos completos: `desktop/ui/views/pagos/estado_cuenta_view.py` y `desktop/controllers/reporte_controller.py` (para ver cómo se genera PDF con reportlab en este proyecto). Luego modifica únicamente `desktop/ui/views/pagos/estado_cuenta_view.py`:
1. Localiza el método `funcion_pendiente_pdf` (o el botón que lo llama).
2. Reemplaza el método vacío por una implementación que use los datos ya cargados en la vista para generar un PDF con reportlab (tabla de movimientos, total pagado, saldo pendiente) y abra `filedialog.asksaveasfilename` para guardar.
3. No llames a la API de nuevo; usa los datos ya cargados en la vista.
No modifiques ningún otro archivo.

---

### [ ] SIN IMPL. 7 — Cursos disponibles para docentes: obtener de la API en vez de lista fija

**INSTRUCCIÓN PARA LA IA:**
Abre únicamente `desktop/controllers/docentes_controller.py`. Localiza el método `obtener_cursos_disponibles`. Actualmente retorna una lista Python hardcodeada. Reemplaza ese método para que llame a `CursosClient` (si no está instanciado en la clase, agrégalo en `__init__` como `self._cursos_client = CursosClient(token)`). Retorna la lista de nombres de cursos obtenida de la API. Si la API falla, retorna la lista hardcodeada como fallback. No modifiques ningún otro archivo.

---

## 🟡 CATEGORÍA 3 — ERRORES DE AUTENTICACIÓN SILENCIOSOS

---

### [ ] AUTH 1 al 6 — Pasar token a todos los controllers que no lo reciben

**INSTRUCCIÓN PARA LA IA:**
Lee completo `desktop/ui/main_window.py`. Luego lee cada uno de estos archivos para ver cómo instancian su controlador:
- `desktop/ui/views/asistencia/reporte_asistencia_view.py`
- `desktop/ui/views/asistencia/reporte_inasistencia_view.py`
- `desktop/ui/views/asistencia/reporte_tardanza_view.py`
- `desktop/ui/views/reportes/gen_carnet.py`
- `desktop/ui/views/reportes/rep_listas.py`
- `desktop/ui/views/academico/doc_constancias.py`

En cada vista donde el controlador se instancia sin token (`MiController()` en lugar de `MiController(auth_client.token)`), haz estos cambios:
1. En la vista: agrega `auth_client` al `__init__` de la vista y pasa `auth_client.token` al controller.
2. En el controller correspondiente: si su `__init__` no acepta `token`, agrégalo como primer parámetro.
3. En `main_window.py`: en el método `show_*` de cada vista afectada, pasa `self.auth_client` al instanciar la vista.
No cambies la lógica de negocio, solo el pasaje del token.

---

## 🟡 CATEGORÍA 4 — INCONSISTENCIAS DE DATOS

---

### [ ] INCONS. 1 — Cambiar "FALTA" por "INASISTENCIA" en `asistencia_controller.py`

**INSTRUCCIÓN PARA LA IA:**
Abre únicamente `desktop/controllers/asistencia_controller.py`. Busca la constante `ESTADO_FALTA` o cualquier string literal `"FALTA"` usado como valor del campo `estado` al registrar o filtrar asistencias. Cámbialo a `"INASISTENCIA"`. El backend solo acepta: `"PUNTUAL"`, `"TARDANZA"`, `"INASISTENCIA"`. No modifiques ninguna otra lógica ni ningún otro archivo.

---

### [ ] INCONS. 2 — Corregir mapeo de campo `celular_padre_1` en AlumnoDTO

**INSTRUCCIÓN PARA LA IA:**
Busca en el proyecto donde está definido `AlumnoDTO` (revisa `desktop/infrastructure/` y `desktop/domain/`). Localiza el campo mapeado como `telefono_apoderado`. La API devuelve ese dato con el nombre `celular_padre_1`. Corrige el mapeo para que use `celular_padre_1`. Luego en `desktop/controllers/carnet_controller.py` y `desktop/controllers/constancia_controller.py` busca referencias a `telefono_apoderado` y cámbialas por `celular_padre_1`. No modifiques ningún otro archivo.

---

### [ ] INCONS. 3 — Carreras por grupo: obtener de la API en vez de dict hardcodeado

**INSTRUCCIÓN PARA LA IA:**
Abre `desktop/controllers/alumno_controller.py`. Localiza el diccionario `CARRERAS_POR_GRUPO` hardcodeado. Reemplaza el método `get_carreras_por_grupo(self, grupo)` para que llame a `GET /cursos/por-grupo/{grupo}` usando `CursosClient(self.token)` y retorne la lista de nombres de cursos. Si la API falla, usa el dict hardcodeado como fallback. No modifiques ningún otro archivo.

---

### [ ] INCONS. 4 — Botón de Configuración nunca se activa en el sidebar

**INSTRUCCIÓN PARA LA IA:**
Abre únicamente `desktop/ui/main_window.py`. Busca todos los métodos cuyo nombre empiece con `show_config_`. En cada uno de esos métodos hay una llamada `self.set_active_nav("configuracion")`. Cámbiala a `self.set_active_nav("config")` en todos los métodos `show_config_*`. No modifiques ninguna otra línea ni ningún otro archivo.

---

### [ ] INCONS. 5 — Vista lista de alumnos debe usar controller en vez de cliente directo

**INSTRUCCIÓN PARA LA IA:**
Lee completo `desktop/ui/views/alumnos/alumnos_list_view.py` y `desktop/controllers/alumno_controller.py`. La vista instancia directamente `AlumnoClient()` y `MatriculasClient()`. Refactorízala para que reciba `auth_client` en su `__init__` y use `AlumnoController(auth_client.token)`. Reemplaza las llamadas directas al cliente por llamadas al controller existente. No cambies la lógica de visualización ni la tabla. No modifiques el controller ni ningún otro archivo.

---

## 🔐 CATEGORÍA 5 — SEGURIDAD

---

### [ ] SEG. 1 — Crear archivo `.env` con claves JWT reales para el backend

**⚠️ ACCIÓN MANUAL DEL DESARROLLADOR — NO EJECUTAR CON IA**
1. Abre terminal en carpeta `backend/`.
2. Genera dos claves: `python -c "import secrets; print(secrets.token_hex(32))"`
3. Copia `backend/.env.example` como `backend/.env`.
4. Reemplaza `SECRET_KEY`, `REFRESH_SECRET_KEY` y `DATABASE_URL` con valores reales.
5. Cambia `ALLOWED_ORIGINS` a la IP del servidor/clientes.

**ESTADO:** Acción manual pendiente.

---

### [ ] SEG. 2 — Cifrar `session.json` para no guardar el token en texto plano

**INSTRUCCIÓN PARA LA IA:**
Lee completo `desktop/core/auth_manager.py`. Modifica únicamente los métodos `save_session` y `load_session` para que cifren/descifren el contenido del archivo usando `cryptography.fernet.Fernet`. La clave de cifrado debe derivarse de `os.getlogin()` con una sal fija usando `hashlib.sha256` y codificada en base64 para que sea reproducible entre reinicios. Si el archivo no puede descifrarse (sesión antigua sin cifrar), trátalo como sesión inválida y retorna `False`. Agrega `cryptography` a `desktop/requirements.txt`. No modifiques ningún otro archivo.

---

### [ ] SEG. 3 — Eliminar credenciales hardcodeadas del código fuente

**INSTRUCCIÓN PARA LA IA:**
Abre únicamente `desktop/core/config.py`. Elimina las líneas que definen `DEFAULT_USER` y `DEFAULT_PASS`. Luego abre `desktop/ui/login_window.py` y elimina cualquier referencia a `Config.DEFAULT_USER` o `Config.DEFAULT_PASS` (no rellenes los campos automáticamente). No modifiques ningún otro archivo.

---

### [ ] SEG. 4 — Asegurar que `refresh_token` siempre se guarde en `session.json`

**INSTRUCCIÓN PARA LA IA:**
Lee completo `desktop/core/auth_manager.py` y `desktop/core/api_client.py` (método `login` de `AuthClient`). Verifica si `AuthClient.login()` retorna el `refresh_token` de la respuesta del backend. Si no lo retorna, modifica `AuthClient.login()` para incluirlo. Verifica que `AuthManager.save_session()` guarde el `refresh_token` cuando se le pasa. Corrige lo que falte. No modifiques ningún otro archivo.

---

## ⚡ CATEGORÍA 6 — RENDIMIENTO

---

### [ ] PERF. 1 — Llamadas HTTP en hilo separado para no bloquear la UI

**INSTRUCCIÓN PARA LA IA (aplica a UNA vista a la vez, especifica cuál):**
Lee completo el archivo de la vista a corregir. Identifica los métodos que llaman a un controller o cliente HTTP directamente en el hilo principal (sin `threading.Thread`). Para cada uno:
1. Crea versión `_nombre_metodo_thread` que haga la llamada HTTP.
2. Lanza en `threading.Thread(target=self._nombre_metodo_thread, daemon=True).start()`.
3. Deshabilita el botón mientras carga, con texto "Cargando...".
4. Usa `self.after(0, callback_con_resultado)` para actualizar la UI desde el hilo principal.
No modifiques el controller ni ningún otro archivo.

---

### [ ] PERF. 2 — Eliminar patrón N+1 en reporte de inasistencias

**INSTRUCCIÓN PARA LA IA:**
Lee completo `desktop/controllers/reporte_inasistencia_controller.py`. El método `obtener_inasistencias_dia` hace una llamada a `GET /matriculas/` por cada alumno. Modifícalo para que:
1. Traiga todas las inasistencias del día con UNA llamada: `GET /asistencia/?fecha=X&estado=INASISTENCIA`.
2. Extraiga todos los `alumno_id` únicos.
3. Traiga todas las matrículas con UNA sola llamada: `GET /matriculas/?estado=activo&limit=1000`.
4. Haga el cruce en memoria con un dict Python.
No modifiques ningún otro archivo.

---

## 🏗️ CATEGORÍA 7 — ARQUITECTURA

---

### [ ] ARQU. 1 — Crear endpoint transaccional `POST /alumnos/completo` en el backend

**INSTRUCCIÓN PARA LA IA:**
Lee estos archivos completos: `backend/app/api/routes/alumnos.py`, `backend/app/services/alumno_service.py`, `backend/app/schemas/alumno.py`, `backend/app/schemas/matricula.py`, `backend/app/schemas/obligacion.py`. Luego:
1. En `backend/app/schemas/alumno.py` agrega schema `AlumnoCompleto` que combine `AlumnoCreate` + campos de `MatriculaCreate` + campos de `ObligacionCreate`.
2. En `backend/app/services/alumno_service.py` agrega método `crear_completo(db, data, creado_por)` que en una sola transacción cree alumno, matrícula y obligación con rollback automático si falla cualquier paso.
3. En `backend/app/api/routes/alumnos.py` agrega endpoint `POST /alumnos/completo` que llame ese servicio.
4. En `desktop/controllers/alumno_controller.py` reemplaza las 3 llamadas separadas por una sola llamada a `POST /alumnos/completo`.
Solo modifica esos 4 archivos, nada más.

---

### [ ] ARQU. 2 — Decidir y limpiar arquitectura de capas en desktop

**⚠️ DECISIÓN REQUERIDA POR EL DESARROLLADOR**
Opción A: Eliminar `desktop/infrastructure/` y `desktop/domain/`, centralizar en `desktop/controllers/`.
Opción B: Completar la arquitectura limpia moviendo clientes de `desktop/core/` a `desktop/infrastructure/`.
Elige una opción y reescribe esta instrucción antes de dársela a la IA.

**ESTADO:** Pendiente de decisión.

---

### [ ] ARQU. 3 — Rate limiting de login con almacenamiento persistente

**INSTRUCCIÓN PARA LA IA:**
Lee completo `backend/app/api/routes/auth.py`. El rate limiter usa un `dict` en memoria Python (`_login_attempts`). Reemplázalo por uno que use un archivo JSON en disco con `filelock` para que funcione entre múltiples workers. Usa `%TEMP%/musuq_rate_limit.json` en Windows o `/tmp/musuq_rate_limit.json` en Linux (detecta el SO con `platform.system()`). Agrega `filelock` a `backend/requirements.txt`. No modifiques ningún otro archivo.

---

### [ ] ARQU. 4 — Crear `config.json` en desktop con la URL real del servidor cloud

**⚠️ ACCIÓN MANUAL DEL DESARROLLADOR — NO EJECUTAR CON IA**
Crea manualmente `desktop/config.json`:
```json
{
    "api_url": "http://TU_IP_O_DOMINIO:8000"
}
```
Reemplaza con la URL real del servidor. Incluye este archivo en el instalador.

**ESTADO:** Acción manual pendiente — requiere conocer la URL del servidor.

---

### [ ] ARQU. 5 — Eliminar controller duplicado que ninguna vista usa

**INSTRUCCIÓN PARA LA IA:**
Busca en todos los archivos `.py` de `desktop/` si hay alguna importación o referencia a `AlumnoControllerRefactorizado` o al archivo `alumno_controller_refactorizado`. Si no hay ninguna referencia en ningún archivo (excepto el propio archivo), elimina `desktop/controllers/alumno_controller_refactorizado.py`. No modifiques ningún otro archivo.

---

## 📊 RESUMEN DE PROGRESO

| Categoría | Total | Resueltos | Pendientes |
|---|---|---|---|
| 🔴 Crashes garantizados | 4 | 0 | 4 |
| 🟠 Sin implementar | 7 | 0 | 7 |
| 🟡 Auth silenciosa (agrupado) | 1 | 0 | 1 |
| 🟡 Inconsistencias de datos | 5 | 0 | 5 |
| 🔐 Seguridad | 4 | 0 | 4 |
| ⚡ Rendimiento | 2 | 0 | 2 |
| 🏗️ Arquitectura | 5 | 0 | 5 |
| **TOTAL** | **28** | **0** | **28** |

---

## 📋 ORDEN DE TRABAJO SUGERIDO

### Fase 1 — Arreglar crashes (mayor impacto, menor riesgo)
1. CRASH 2 — prefijo `desktop.` incorrecto en import constancias
2. CRASH 3 — alias `TM` incorrecto en `doc_constancias.py`
3. CRASH 4 — `landscape(card_size=...)` inválido en `carnet_controller.py`
4. CRASH 1 — crear archivo `resumen_docentes_view.py`

### Fase 2 — Datos incorrectos
5. INCONS. 1 — `"FALTA"` → `"INASISTENCIA"`
6. INCONS. 4 — `"configuracion"` → `"config"` en sidebar
7. INCONS. 2 — mapeo `celular_padre_1` en DTO
8. SIN IMPL. 4 — boletas con notas reales
9. SIN IMPL. 7 — cursos de docentes desde API

### Fase 3 — Autenticación
10. AUTH 1 al 6 — token en todos los controllers

### Fase 4 — Implementaciones pendientes
11. SIN IMPL. 1 — periodos lectivos a la API
12. SIN IMPL. 5 — historial de alumno
13. SIN IMPL. 6 — PDF estado de cuenta
14. INCONS. 3 — carreras desde API
15. INCONS. 5 — lista alumnos usa controller

### Fase 5 — Seguridad (antes de producción)
16. SEG. 1 — `backend/.env` ⚠️ manual
17. SEG. 3 — eliminar credenciales hardcodeadas
18. SEG. 4 — guardar `refresh_token`
19. ARQU. 4 — `desktop/config.json` ⚠️ manual
20. SEG. 2 — cifrar `session.json`

### Fase 6 — Arquitectura y rendimiento
21. ARQU. 5 — eliminar controller duplicado
22. ARQU. 1 — endpoint transaccional
23. PERF. 2 — eliminar N+1
24. PERF. 1 — HTTP en hilos (vista por vista)
25. ARQU. 3 — rate limiting persistente
26. ARQU. 2 — limpiar arquitectura ⚠️ decidir primero
