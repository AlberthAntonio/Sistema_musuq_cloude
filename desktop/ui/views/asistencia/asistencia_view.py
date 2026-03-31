"""

Vista de Control de Asistencia (Modo Kiosco) - ESTILO MEJORADO

Sistema Musuq Cloud

"""

import customtkinter as ctk
from tkinter import messagebox
import threading
import locale
from datetime import datetime, time as dt_time
from core.api_client import APIClient
from controllers.asistencia_controller import AsistenciaController
from utils.audio_helper import AudioHelper
from styles import tabla_style as st
from core.theme_manager import ThemeManager as TM
from mixins.infinite_scroll_mixin import InfiniteScrollMixin
from ui.dialogs.dialogo_alerta_turno import DialogoAlertaTurno
from ui.dialogs.dialogo_inasistencias import DialogoInasistencias
from utils.perf_utils import get_logger

logger = get_logger(__name__)

# Intentar poner fechas en español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    pass

class AsistenciaView(ctk.CTkFrame, InfiniteScrollMixin):
    """
    Vista principal de asistencia con diseño tipo Kiosco.
    Permite escaneo de códigos, búsqueda y visualización de historial.
    """

    def __init__(self, parent, auth_client: APIClient):
        super().__init__(parent, fg_color="transparent")
        self.controller = AsistenciaController(auth_client.token)
        self.audio = AudioHelper()

        # Variables de estado
        self.fila_seleccionada = None
        self.datos_seleccionados = None
        self.color_original_seleccion = None
        self._reloj_after = None
        self.turno_actual_cache = self._obtener_turno_actual()
        self.filtro_turno_activo = True
        self._monitor_turno_after = None
        self._turno_display_after = None
        self.primer_widget_fila = None
        self.cargando = False
        self.registros_cache = []
        self._debounce_timer = None
        self._is_visible = True  # Flag de visibilidad para ciclo de vida
        self._pending_afters = []  # Track de after IDs pendientes

        # Anchos de columnas
        self.ANCHOS = [0, 100, 300, 80, 100, 100]

        self.create_widgets()

        # Iniciar procesos que no dependen de datos
        self.actualizar_reloj()
        self.actualizar_turno_display()
        self._verificar_cambio_turno()

        # Cargar cache de nombres PRIMERO, luego tabla
        threading.Thread(target=self._iniciar_carga_datos, daemon=True).start()

        # Foco inicial
        self.after(500, lambda: self.entry_codigo.focus())

    def create_widgets(self):
        # Grid Principal
        self.grid_columnconfigure(0, weight=7)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # ==================== COLUMNA IZQUIERDA (INPUT + TABLA) ====================
        self.card_izq = ctk.CTkFrame(self, fg_color="transparent", corner_radius=10)
        self.card_izq.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        self.card_izq.grid_rowconfigure(4, weight=1)
        self.card_izq.grid_columnconfigure(0, weight=1)

        # 1. Encabezado con mejor diseño
        header_frame = ctk.CTkFrame(self.card_izq, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 15))

        self.lbl_titulo = ctk.CTkLabel(
            header_frame,
            text="📋 CONTROL DE ASISTENCIA",
            font=ctk.CTkFont(family="Roboto", size=20, weight="bold"),
            text_color=TM.text()
        )
        self.lbl_titulo.pack(side="left")

        self.lbl_instr = ctk.CTkLabel(
            header_frame,
            text="Ingrese CÓDIGO o escanee carnet ➝",
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        )
        self.lbl_instr.pack(side="right")

        # 2. Input Principal con mejor diseño
        self.fr_input = ctk.CTkFrame(self.card_izq, fg_color="transparent")
        self.fr_input.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 10))

        self.entry_codigo = ctk.CTkEntry(
            self.fr_input,
            placeholder_text="📷 Código aquí...",
            height=50,
            font=ctk.CTkFont(family="Roboto", size=24, weight="bold"),
            border_width=0,
            fg_color=TM.bg_panel(),
            text_color=TM.text(),
            justify="center",
            corner_radius=10
        )
        self.entry_codigo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_codigo.bind("<Return>", self.registrar_asistencia)

        self.btn_marcar = ctk.CTkButton(
            self.fr_input,
            text="MARCAR",
            width=120,
            height=50,
            fg_color=st.Colors.ASISTENCIA,
            hover_color="#2980b9",
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
            corner_radius=10,
            command=self.registrar_asistencia
        )
        self.btn_marcar.pack(side="right")

        # 3. Barra de Búsqueda mejorada (estilo alumnos_list)
        self.fr_busqueda = ctk.CTkFrame(
            self.card_izq,
            height=50,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.fr_busqueda.grid(row=2, column=0, sticky="ew", padx=0, pady=(5, 10))

        ctk.CTkLabel(
            self.fr_busqueda,
            text="🔍",
            font=ctk.CTkFont(size=14),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(15, 5))

        self.entry_busqueda = ctk.CTkEntry(
            self.fr_busqueda,
            placeholder_text="Buscar por Nombre, DNI o Código...",
            height=35,
            border_width=0,
            fg_color=TM.bg_panel(),
            text_color=TM.text(),
            corner_radius=8
        )
        self.entry_busqueda.pack(side="left", fill="x", expand=True, padx=5, pady=8)
        self.entry_busqueda.bind("<KeyRelease>", self.evento_buscar_alumno)

        # 4. Lista de Resultados Búsqueda
        self.wrapper_resultados = ctk.CTkFrame(self.card_izq, fg_color="transparent", height=0)
        self.fr_resultados = ctk.CTkScrollableFrame(
            self.wrapper_resultados,
            fg_color=TM.bg_card(),
            height=100
        )
        self.fr_resultados.pack(fill="both", expand=True)

        self.lbl_busqueda_loading = ctk.CTkLabel(
            self.fr_resultados,
            text="🔍 Buscando...",
            text_color=TM.text_secondary()
        )

        self.lbl_busqueda_empty = ctk.CTkLabel(
            self.fr_resultados,
            text="⚠️ No se encontraron coincidencias",
            text_color=TM.text_secondary()
        )

        # 5. Tabla Historial con diseño mejorado
        self.fr_tabla = ctk.CTkFrame(self.card_izq, fg_color="transparent")
        self.fr_tabla.grid(row=4, column=0, sticky="nsew", padx=0, pady=(5, 0))

        # Header Tabla mejorado
        self.fr_header_tabla = ctk.CTkFrame(self.fr_tabla, fg_color="transparent")
        self.fr_header_tabla.pack(fill="x", pady=(0, 10))

        fr_info_izq = ctk.CTkFrame(self.fr_header_tabla, fg_color="transparent")
        fr_info_izq.pack(side="left")

        ctk.CTkLabel(
            fr_info_izq,
            text="HISTORIAL DE HOY",
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(side="left")

        self.lbl_contador = ctk.CTkLabel(
            fr_info_izq,
            text="(0/0)",
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=TM.primary(),
            fg_color=TM.bg_panel(),
            corner_radius=5,
            padx=8, pady=2
        )
        self.lbl_contador.pack(side="left", padx=10)

        self.switch_filtro = ctk.CTkSwitch(
            fr_info_izq,
            text="Filtrar turno",
            font=ctk.CTkFont(family="Roboto", size=9),
            command=self.toggle_filtro_turno,
            width=80, height=20, switch_width=35, switch_height=18
        )
        self.switch_filtro.pack(side="left", padx=10)
        self.switch_filtro.select()

        self.lbl_loader = ctk.CTkLabel(
            self.fr_header_tabla,
            text="⏳ Cargando...",
            text_color=TM.warning()
        )

        # Contenedor tabla con estilo alumnos_list
        self.container_list = ctk.CTkFrame(
            self.fr_tabla,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.container_list.pack(fill="both", expand=True)

        self.crear_cabecera()

        self.scroll_tabla = ctk.CTkScrollableFrame(
            self.container_list,
            fg_color="transparent"
        )
        self.scroll_tabla.pack(fill="both", expand=True, padx=5, pady=5)

        # Inicializar Mixin
        self.init_infinite_scroll(self.scroll_tabla, lote_tamano=25)

        # ==================== COLUMNA DERECHA (ESTADO + RELOJ) ====================
        self.card_der = ctk.CTkFrame(
            self,
            width=250,
            fg_color=TM.bg_card(),
            corner_radius=15
        )
        self.card_der.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)

        # Reloj
        self.fr_reloj = ctk.CTkFrame(self.card_der, fg_color="transparent")
        self.fr_reloj.pack(pady=(40, 10), fill="x")

        self.lbl_reloj = ctk.CTkLabel(
            self.fr_reloj,
            text="00:00:00",
            font=ctk.CTkFont(family="Roboto", size=42, weight="bold"),
            text_color=TM.text()
        )
        self.lbl_reloj.pack()

        self.lbl_fecha = ctk.CTkLabel(
            self.fr_reloj,
            text="--/--/----",
            font=ctk.CTkFont(family="Roboto", size=13),
            text_color=TM.warning()
        )
        self.lbl_fecha.pack()

        # Turno
        self.lbl_turno_activo = ctk.CTkLabel(
            self.card_der,
            text=self._obtener_turno_actual(),
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=TM.primary(),
            fg_color=TM.bg_panel(),
            corner_radius=8,
            height=35
        )
        self.lbl_turno_activo.pack(pady=(10, 5), padx=20, fill="x")

        # Estado (Grande)
        self.lbl_estado = ctk.CTkLabel(
            self.card_der,
            text="ESPERANDO...",
            width=200,
            height=70,
            corner_radius=15,
            fg_color=TM.bg_panel(),
            text_color=TM.text_secondary(),
            font=ctk.CTkFont(family="Roboto", size=18, weight="bold")
        )
        self.lbl_estado.pack(pady=(20, 30), padx=20)

        # Botones Acción con estilo mejorado
        ctk.CTkLabel(
            self.card_der,
            text="ACCIONES",
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(pady=(20, 15))

        self.fr_botones = ctk.CTkFrame(self.card_der, fg_color="transparent")
        self.fr_botones.pack(fill="both", expand=True, padx=20, pady=5)

        self.btn_limpiar = ctk.CTkButton(
            self.fr_botones,
            text="🧹 REFRESCAR TABLA",
            height=40,
            fg_color="#404040",
            hover_color="#505050",
            command=self.cargar_tabla_thread
        )
        self.btn_limpiar.pack(fill="x", pady=5)

        self.btn_inasistencias = ctk.CTkButton(
            self.fr_botones,
            text="📋 MARCAR INASISTENCIAS",
            height=40,
            fg_color="#6c3483",
            hover_color="#7d3c98",
            command=self.confirmar_marcar_inasistencias
        )
        self.btn_inasistencias.pack(fill="x", pady=5)

        self.btn_eliminar = ctk.CTkButton(
            self.fr_botones,
            text="🗑️ ELIMINAR",
            height=40,
            fg_color=TM.danger(),
            hover_color="#c0392b",
            state="disabled",
            command=self.eliminar_seleccion
        )
        self.btn_eliminar.pack(fill="x", pady=5)

    # ================= MÉTODOS VISUALES =================

    def crear_cabecera(self):
        header = ctk.CTkFrame(
            self.container_list,
            height=40,
            fg_color=st.Colors.TABLE_HEADER,
            corner_radius=5
        )
        header.pack(fill="x", padx=5, pady=(5, 0))

        fr_columnas = ctk.CTkFrame(header, fg_color="transparent")
        fr_columnas.pack(side="left", padx=5)

        cols = ["", "CÓDIGO", "ALUMNO", "HORARIO", "ESTADO", "HORA"]

        for i, t in enumerate(cols):
            if i == 0:
                continue
            w = self.ANCHOS[i]
            ctk.CTkLabel(
                fr_columnas,
                text=t,
                font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
                text_color="white",
                width=w
            ).pack(side="left", padx=2)

    def actualizar_reloj(self):
        if not self.winfo_exists() or not self._is_visible:
            return

        now = datetime.now()
        self.lbl_reloj.configure(text=now.strftime("%H:%M:%S"))
        self.lbl_fecha.configure(text=now.strftime("%A, %d de %B del %Y").upper())

        self._reloj_after = self.after(1000, self.actualizar_reloj)

    def _obtener_turno_actual(self):
        hora_actual = datetime.now().time()
        if dt_time(6, 0, 0) <= hora_actual < dt_time(13, 0, 0):
            return "🌅 TURNO MAÑANA ACTIVO"
        elif dt_time(13, 0, 0) <= hora_actual <= dt_time(23, 59, 59):
            return "🌆 TURNO TARDE ACTIVO"
        else:
            return "⏸️ FUERA DE HORARIO"

    def actualizar_turno_display(self):
        if not self.winfo_exists() or not self._is_visible:
            return

        self.lbl_turno_activo.configure(text=self._obtener_turno_actual())
        self._turno_display_after = self.after(60000, self.actualizar_turno_display)

    def toggle_filtro_turno(self):
        self.filtro_turno_activo = self.switch_filtro.get()
        self.switch_filtro.configure(
            text="🔍 Solo turno actual" if self.filtro_turno_activo else "📋 Viendo todos"
        )
        self.cargar_tabla_thread()

    # ================= LÓGICA DE DATOS =================

    def cargar_tabla_thread(self):
        logger.debug("cargar_tabla_thread llamado")
        self.lbl_loader.pack(side="right", padx=10)
        self.btn_limpiar.configure(state="disabled")
        self.limpiar_scroll()
        threading.Thread(target=self._cargar_datos, daemon=True).start()

    def _cargar_datos(self):
        success, result = self.controller.asistencia_client.obtener_hoy()

        if success:
            registros = result if isinstance(result, list) else result.get("items", [])

            if self.filtro_turno_activo:
                turno_actual_short = "MAÑANA" if "MAÑANA" in self._obtener_turno_actual() else "TARDE"
                registros = [r for r in registros if r.get("turno") == turno_actual_short]

            registros.sort(key=lambda x: x.get("hora") or "", reverse=True)
            self.after(0, lambda: self._inicializar_tabla(registros))
        else:
            self.after(0, lambda: self._error_carga())

    def _inicializar_tabla(self, registros):
        if not self.winfo_exists():
            return
        logger.debug(f"Inicializando tabla con {len(registros)} registros")
        self.lbl_loader.pack_forget()
        self.btn_limpiar.configure(state="normal")

        self.cargar_datos_scroll(registros)

        # Actualizar contador con lógica de color
        actual = len(registros)

        if self.filtro_turno_activo:
            turno_actual_str = self._obtener_turno_actual()
            if "MAÑANA" in turno_actual_str:
                turno = "MAÑANA"
            elif "TARDE" in turno_actual_str:
                turno = "TARDE"
            else:
                turno = None

            if turno:
                total = self._calcular_total_esperado(turno)
            else:
                total = self.controller.contar_todos_alumnos()
        else:
            total = self.controller.contar_todos_alumnos()

        # Determinar color según si excede el total
        if actual > total:
            color = TM.danger()
            icono = "⚠️"
        elif actual == total:
            color = TM.success()
            icono = "✅"
        else:
            color = TM.primary()
            icono = "📊"

        self.lbl_contador.configure(
            text=f"{icono} {actual}/{total}",
            text_color=color
        )

    def _verificar_cambio_turno(self):
        """Verifica cambio de turno y recarga automáticamente si está filtrado"""
        if not self.winfo_exists():
            return

        turno_nuevo = self._obtener_turno_actual()

        if turno_nuevo != self.turno_actual_cache:
            if self.filtro_turno_activo:
                self.cargar_tabla_thread()

            self.lbl_estado.configure(
                text=f"🔄 {turno_nuevo}",
                fg_color=TM.primary(),
                text_color="white"
            )

            self.after(4000, lambda: self.lbl_estado.configure(
                text="ESPERANDO...",
                fg_color=TM.bg_panel(),
                text_color=TM.text_secondary()
            ) if self.winfo_exists() else None)

            self.turno_actual_cache = turno_nuevo
            self.actualizar_turno_display()

        if self.winfo_exists() and self._is_visible:
            self._monitor_turno_after = self.after(60000, self._verificar_cambio_turno)

    def _calcular_total_esperado(self, turno):
        """
        Calcula cuántos alumnos DEBEN asistir al turno especificado.
        El turno (MAÑANA/TARDE) determina qué horarios (MATUTINO/VESPERTINO/DOBLE HORARIO)
        se deben contabilizar.
        Args:
            turno: "MAÑANA" o "TARDE"
        """
        try:
            if turno == "MAÑANA":
                return self.controller.contar_alumnos_por_horario("MATUTINO", "DOBLE HORARIO")
            elif turno == "TARDE":
                return self.controller.contar_alumnos_por_horario("VESPERTINO", "DOBLE HORARIO")
            else:
                return self.controller.contar_todos_alumnos()
        except Exception:
            return 0

    def _error_carga(self):
        self.lbl_loader.pack_forget()
        self.btn_limpiar.configure(state="normal")
        messagebox.showerror("Error", "No se pudieron cargar los registros")

    # ================= REGISTRO DE ASISTENCIA =================

    def registrar_asistencia(self, event=None, forzar_turno_cruzado: bool = False, _codigo_prefijo: str = ""):
        codigo = _codigo_prefijo or self.entry_codigo.get().strip()
        if not codigo:
            return

        self.entry_codigo.configure(state="disabled")
        self.btn_marcar.configure(state="disabled")
        self.lbl_estado.configure(
            text="PROCESANDO...",
            fg_color=TM.warning(),
            text_color="white"
        )

        threading.Thread(
            target=self._hilo_registrar,
            args=(codigo, forzar_turno_cruzado),
            daemon=True
        ).start()

    def _hilo_registrar(self, codigo: str, forzar_turno_cruzado: bool = False):
        exito, mensaje, datos, alerta_turno = self.controller.registrar_por_dni(
            codigo, forzar_turno_cruzado=forzar_turno_cruzado
        )
        self.after(0, lambda: self._post_registro(exito, mensaje, datos, alerta_turno, codigo))

    def _post_registro(self, exito, mensaje, datos, alerta_turno, codigo_original: str = ""):
        self.entry_codigo.configure(state="normal")
        self.entry_codigo.delete(0, 'end')
        self.entry_codigo.focus()
        self.btn_marcar.configure(state="normal")

        # ── Caso especial: turno cruzado detectado, aún NO registrado ──
        if not exito and mensaje == "TURNO_CRUZADO_PENDIENTE":
            self._mostrar_dialogo_turno_cruzado(datos, codigo_original)
            return

        if not exito:
            self.lbl_estado.configure(
                text="❌ ERROR",
                fg_color=st.Colors.FALTA,
                text_color="white"
            )
            self.audio.reproducir_alerta_error()
            messagebox.showerror("Error", mensaje)
            self._reset_estado()
        else:
            nombre = datos.get("alumno", {}).get("nombres", "Alumno")

            if alerta_turno:
                # Registro forzado tras confirmación del personal
                self.lbl_estado.configure(
                    text=f"⚠️ TURNO CRUZADO\n{nombre}",
                    fg_color=st.Colors.TARDANZA,
                    text_color="white"
                )
            else:
                self.lbl_estado.configure(
                    text=f"✅ REGISTRADO\n{nombre}",
                    fg_color=st.Colors.PUNTUAL,
                    text_color="white"
                )
                self.audio.reproducir_registro_exitoso()

            self.cargar_tabla_thread()
            self._reset_estado(delay=3000)

    def _mostrar_dialogo_turno_cruzado(self, datos: dict, codigo_original: str):
        """
        Muestra el diálogo modal de turno cruzado.
        - Si el personal CONFIRMA → relanza el registro con forzar=True.
        - Si RECHAZA → cancela y restaura estado.
        """
        # Actualizar estado visual
        self.lbl_estado.configure(
            text="⚠️ TURNO CRUZADO",
            fg_color=st.Colors.TARDANZA,
            text_color="white"
        )

        # ── Disparar alarma ANTES del grab_set() del diálogo ──────────
        # grab_set() captura eventos del SO y puede silenciar winsound
        self.audio.reproducir_alerta_turno_cruzado()
        self.update()  # forzar render antes de bloquear el event loop

        dialogo = DialogoAlertaTurno(
            parent=self.winfo_toplevel(),
            datos_alumno=datos,
            audio_helper=self.audio
        )
        # wait_window bloquea el event loop hasta que el diálogo se cierre
        self.wait_window(dialogo)

        if dialogo.confirmado:
            # Personal autorizó → registrar con forzar=True
            self.entry_codigo.configure(state="disabled")
            self.btn_marcar.configure(state="disabled")
            self.lbl_estado.configure(
                text="PROCESANDO...",
                fg_color=TM.warning(),
                text_color="white"
            )
            threading.Thread(
                target=self._hilo_registrar,
                args=(codigo_original, True),
                daemon=True
            ).start()
        else:
            # Personal rechazó → cancelar
            self.lbl_estado.configure(
                text="🚫 INGRESO RECHAZADO",
                fg_color=TM.danger(),
                text_color="white"
            )
            self._reset_estado(delay=3000)

    def _reset_estado(self, delay=3000):
        self.after(delay, lambda: self.lbl_estado.configure(
            text="ESPERANDO...",
            fg_color=TM.bg_panel(),
            text_color=TM.text_secondary()
        ) if self.winfo_exists() else None)

    # ================= MARCAR INASISTENCIAS =================

    def confirmar_marcar_inasistencias(self):
        """
        Paso 1: detecta el turno activo y lanza un hilo para obtener el
        resumen previo. Si no hay turno activo, avisa y sale.
        """
        turno_str = self._obtener_turno_actual()
        if "MAÑANA" in turno_str:
            turno = "MAÑANA"
        elif "TARDE" in turno_str:
            turno = "TARDE"
        else:
            messagebox.showwarning(
                "Fuera de horario",
                "No hay un turno activo en este momento.\n"
                "Esta acción solo está disponible dentro del horario escolar."
            )
            return

        # Deshabilitar botón y mostrar estado mientras se calcula el preview
        self.btn_inasistencias.configure(state="disabled", text="⏳ Calculando...")
        self.lbl_estado.configure(
            text="CALCULANDO...",
            fg_color="#6c3483",
            text_color="white"
        )
        threading.Thread(
            target=self._hilo_previsualizar,
            args=(turno,),
            daemon=True
        ).start()

    def _hilo_previsualizar(self, turno: str):
        """Paso 2 (hilo): obtiene el resumen sin registrar nada."""
        exito, msg_error, resumen = self.controller.previsualizar_inasistencias(turno)
        self.after(0, lambda: self._mostrar_dialogo_inasistencias(exito, msg_error, resumen, turno))

    def _mostrar_dialogo_inasistencias(self, exito: bool, msg_error: str, resumen: dict, turno: str):
        """
        Paso 3 (hilo principal): restaura el botón y muestra el diálogo.
        Si el usuario confirma, lanza el hilo de registro.
        """
        self.btn_inasistencias.configure(state="normal", text="📋 MARCAR INASISTENCIAS")

        if not exito:
            self.lbl_estado.configure(
                text="❌ ERROR",
                fg_color=TM.danger(),
                text_color="white"
            )
            messagebox.showerror("Error al calcular resumen", msg_error)
            self._reset_estado()
            return

        self.lbl_estado.configure(
            text="ESPERANDO...",
            fg_color=TM.bg_panel(),
            text_color=TM.text_secondary()
        )

        dialogo = DialogoInasistencias(
            parent=self.winfo_toplevel(),
            resumen=resumen
        )
        self.wait_window(dialogo)

        if dialogo.confirmado:
            self._ejecutar_marcar_inasistencias(turno)

    def _ejecutar_marcar_inasistencias(self, turno: str):
        """Paso 4: lanza el registro masivo en un hilo."""
        self.btn_inasistencias.configure(state="disabled", text="⏳ Registrando...")
        self.lbl_estado.configure(
            text="MARCANDO\nFALTAS...",
            fg_color="#6c3483",
            text_color="white"
        )
        threading.Thread(
            target=self._hilo_inasistencias,
            args=(turno,),
            daemon=True
        ).start()

    def _hilo_inasistencias(self, turno: str):
        """Paso 5 (hilo): ejecuta el registro masivo."""
        exito, mensaje, cantidad = self.controller.marcar_inasistencias_masivo(turno)
        self.after(0, lambda: self._post_inasistencias(exito, mensaje, cantidad))

    def _post_inasistencias(self, exito: bool, mensaje: str, cantidad: int):
        """Paso 6 (hilo principal): muestra resultado y refresca tabla."""
        self.btn_inasistencias.configure(state="normal", text="📋 MARCAR INASISTENCIAS")

        if exito:
            if cantidad == 0:
                self.lbl_estado.configure(
                    text="✅ SIN AUSENTES",
                    fg_color=TM.success(),
                    text_color="white"
                )
            else:
                self.lbl_estado.configure(
                    text=f"📋 {cantidad}\nFALTAS MARCADAS",
                    fg_color="#6c3483",
                    text_color="white"
                )
                self.cargar_tabla_thread()
        else:
            self.lbl_estado.configure(
                text="❌ ERROR",
                fg_color=TM.danger(),
                text_color="white"
            )
            messagebox.showerror("Error", mensaje)

        self._reset_estado(delay=4000)

    def eliminar_seleccion(self):
        if not self.fila_seleccionada or not self.datos_seleccionados:
            return

        id_asist = self.datos_seleccionados.get("id")
        alumno_id = self.datos_seleccionados.get("alumno_id")
        nombre = f"Alumno {alumno_id}"

        if hasattr(self.controller, 'mapa_alumnos') and alumno_id in self.controller.mapa_alumnos:
            a = self.controller.mapa_alumnos[alumno_id]
            nombre = f"{a.get('nombres', '')} {a.get('apell_paterno', '')} {a.get('apell_materno', '')}".strip()

        confirm = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Estás seguro de eliminar la asistencia de:\n\n{nombre}?\n\nEsta acción no se puede deshacer."
        )

        if confirm:
            success, msg = self.controller.eliminar_asistencia(id_asist)

            if success:
                self.lbl_estado.configure(
                    text="🗑️ ELIMINADO",
                    fg_color=TM.danger(),
                    text_color="white"
                )
                self.cargar_tabla_thread()
                self._reset_estado()

                self.fila_seleccionada = None
                self.datos_seleccionados = None
                self.btn_eliminar.configure(state="disabled")
            else:
                messagebox.showerror("Error", msg)

    # ================= BÚSQUEDA =================

    def evento_buscar_alumno(self, event):
        """Evento al escribir en la barra de búsqueda con debounce"""
        # Cancelar timer anterior si existe
        if self._debounce_timer:
            self.after_cancel(self._debounce_timer)
        
        # Programar nueva búsqueda en 500ms
        self._debounce_timer = self.after(500, self._ejecutar_busqueda_alumno)

    def _ejecutar_busqueda_alumno(self):
        """Ejecuta la búsqueda real después del debounce"""
        texto = self.entry_busqueda.get().strip()

        self._limpiar_resultados()

        if len(texto) < 2:
            self.wrapper_resultados.grid_forget()
            return

        self.wrapper_resultados.grid(row=3, column=0, sticky="ew", padx=0, pady=(0, 10))
        self.lbl_busqueda_loading.pack(pady=10)

        threading.Thread(target=self._buscar_hilo, args=(texto,), daemon=True).start()

    def _buscar_hilo(self, texto):
        resultados = self.controller.buscar_alumnos_general(texto)
        if self.winfo_exists():
            self.after(0, lambda: self._mostrar_resultados(resultados))

    def _mostrar_resultados(self, resultados):
        """Mostrar resultados de búsqueda en la UI"""
        if not self.winfo_exists():
            return

        self._limpiar_resultados()

        self.wrapper_resultados.grid(row=3, column=0, sticky="ew", padx=0, pady=(0, 10))
        self.wrapper_resultados.lift()

        if not resultados:
            self.lbl_busqueda_empty.pack(pady=10)
            return

        for i, res in enumerate(resultados[:10]):
            nombre_completo = res.get('nombre_completo', '')
            if not nombre_completo:
                nombre = res.get('nombres', '')
                paterno = res.get('apell_paterno', '')
                materno = res.get('apell_materno', '')
                nombre_completo = f"{nombre} {paterno} {materno}".strip()

            dni = res.get('dni', 'Sin DNI')
            codigo = res.get('codigo_matricula', '')
            grupo = res.get('grupo', '')

            texto_btn = f"👤 {nombre_completo}"
            if dni != 'Sin DNI':
                texto_btn += f" | DNI: {dni}"
            if codigo:
                texto_btn += f" | Cód: {codigo}"
            if grupo:
                texto_btn += f" | [{grupo}]"

            btn = ctk.CTkButton(
                self.fr_resultados,
                text=texto_btn,
                anchor="w",
                fg_color="transparent",
                text_color=TM.text(),
                hover_color=st.Colors.HOVER,
                height=35,
                command=lambda r=res: self._seleccionar_busqueda(r)
            )
            btn.pack(fill="x", pady=1, padx=5)

        if len(resultados) > 10:
            info = ctk.CTkLabel(
                self.fr_resultados,
                text=f"ℹ️ Mostrando 10 de {len(resultados)} resultados. Refina tu búsqueda.",
                text_color=TM.warning(),
                font=ctk.CTkFont(family="Roboto", size=9)
            )
            info.pack(pady=5)

    def _seleccionar_busqueda(self, alumno):
        self.entry_codigo.delete(0, 'end')
        self.entry_codigo.insert(0, alumno.get("dni"))
        self.registrar_asistencia()

        self.entry_busqueda.delete(0, 'end')
        self.wrapper_resultados.grid_forget()
        self._limpiar_resultados()

    def _limpiar_resultados(self):
        """Limpia solo los items de resultados de busqueda."""
        for w in self.fr_resultados.winfo_children():
            if w in (self.lbl_busqueda_loading, self.lbl_busqueda_empty):
                continue
            w.destroy()
        self.lbl_busqueda_loading.pack_forget()
        self.lbl_busqueda_empty.pack_forget()

    # ================= IMPLEMENTACIÓN MIXIN =================

    def render_fila_scroll(self, reg, index):
        """Renderiza una fila de asistencia usando el mixin"""
        if not self.winfo_exists():
            return

        id_asistencia = reg.get("id")
        alumno_id = reg.get("alumno_id")

        # El backend ya devuelve el objeto alumno anidado en la respuesta
        alumno_data = reg.get("alumno") or {}
        if alumno_data:
            nombre = f"{alumno_data.get('nombres', '')} {alumno_data.get('apell_paterno', '')} {alumno_data.get('apell_materno', '')}".strip()
            codigo = alumno_data.get("codigo_matricula") or ""
            horario_raw = alumno_data.get("horario") or ""
        elif hasattr(self.controller, 'mapa_alumnos') and alumno_id in self.controller.mapa_alumnos:
            a = self.controller.mapa_alumnos[alumno_id]
            nombre = f"{a.get('nombres', '')} {a.get('apell_paterno', '')} {a.get('apell_materno', '')}" .strip()
            codigo = a.get("codigo_matricula") or ""
            horario_raw = a.get("horario") or ""
        else:
            nombre = f"Alumno {alumno_id}"
            codigo = ""
            horario_raw = ""

        turno = (reg.get("turno") or "MAÑANA").upper()
        estado = (reg.get("estado") or "PUNTUAL").upper()
        hora = reg.get("hora", "")
        if isinstance(hora, str):
            hora = hora[:8]

        # Colores de fila mejorados (estilo alumnos_list)
        bg = "#2d2d2d" if index % 2 == 0 else "#363636"

        row = ctk.CTkFrame(
            self._scroll_widget_inf,
            fg_color=bg,
            corner_radius=5,
            height=35
        )
        row.bind("<Button-1>", lambda e, r=row, d=reg: self._seleccionar_fila(e, r, d))
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        font_row = ctk.CTkFont(family="Roboto", size=11)

        def lbl(txt, w, col, anchor="center"):
            l = ctk.CTkLabel(
                row,
                text=str(txt),
                width=w,
                text_color=col,
                font=font_row,
                anchor=anchor
            )
            l.pack(side="left", padx=2)
            l.bind("<Button-1>", lambda e, r=row, d=reg: self._seleccionar_fila(e, r, d))

        lbl(codigo, self.ANCHOS[1], TM.text_secondary())
        lbl(nombre.upper(), self.ANCHOS[2], TM.text(), "w")

        # Horario del alumno: MATUTINO → M, VESPERTINO → V, DOBLE HORARIO → DH
        h = horario_raw.upper()
        if "DOBLE" in h:
            horario_label = "DH"
            horario_color = TM.warning()
        elif "VESPERTINO" in h or h.startswith("V"):
            horario_label = "V"
            horario_color = "#9b59b6"
        elif "MATUTINO" in h or h.startswith("M"):
            horario_label = "M"
            horario_color = TM.primary()
        else:
            horario_label = "?"
            horario_color = TM.text_secondary()
        lbl(horario_label, self.ANCHOS[3], horario_color)

        # Badge Estado — backend devuelve: "Puntual", "Tarde", "Falta"
        bg_st = TM.bg_panel()
        estado_u = estado.upper()
        if "PUNTUAL" in estado_u:
            bg_st = st.Colors.PUNTUAL
        elif "TARD" in estado_u:  # "Tarde" o "TARDANZA"
            bg_st = st.Colors.TARDANZA
        elif "FALTA" in estado_u or "INASIST" in estado_u:
            bg_st = st.Colors.FALTA

        f_st = ctk.CTkFrame(row, fg_color="transparent", width=self.ANCHOS[4], height=35)
        f_st.pack(side="left", padx=2)
        ctk.CTkLabel(
            f_st,
            text=estado_u,
            fg_color=bg_st,
            text_color="white",
            width=80,
            height=20,
            corner_radius=5
        ).place(relx=0.5, rely=0.5, anchor="center")

        lbl(hora, self.ANCHOS[5], TM.text_secondary())

    def _iniciar_carga_datos(self):
        """Carga cache de nombres PRIMERO, luego la tabla"""
        self._cargar_cache_nombres()
        if self.winfo_exists():
            self.after(0, self.cargar_tabla_thread)

    def _cargar_cache_nombres(self):
        """Helper para traer lista de alumnos y poder mostrar nombres"""
        success, res = self.controller.alumno_client.obtener_todos(limit=2000)

        if success:
            items = res if isinstance(res, list) else res.get("items", [])
            self.controller.mapa_alumnos = {a['id']: a for a in items}
            logger.debug(f"Cache de nombres cargado: {len(self.controller.mapa_alumnos)} alumnos")

    def _seleccionar_fila(self, event, row_widget, data):
        """Maneja la selección visual de una fila"""
        if self.fila_seleccionada and self.fila_seleccionada.winfo_exists():
            try:
                self.fila_seleccionada.configure(fg_color=self.color_original_seleccion)
            except:
                pass

        self.fila_seleccionada = row_widget
        self.datos_seleccionados = data
        self.color_original_seleccion = row_widget._fg_color

        # Color de selección consistente con alumnos_list
        row_widget.configure(fg_color="#34495e")

        self.btn_eliminar.configure(state="normal")

    # ================= CICLO DE VIDA =================

    def on_show(self):
        """Llamado cuando la vista se hace visible (ciclo de vida)"""
        self._is_visible = True
        # Relanzar timers solo si estaban detenidos
        if self._reloj_after is None:
            self.actualizar_reloj()
        if self._monitor_turno_after is None:
            self._verificar_cambio_turno()
        if self._turno_display_after is None:
            self.actualizar_turno_display()

    def on_hide(self):
        """Llamado cuando la vista se oculta (ciclo de vida)"""
        self._is_visible = False
        self._cancel_all_timers()

    def cleanup(self):
        """Limpieza total al destruir la vista (logout)"""
        self._is_visible = False
        self._cancel_all_timers()

    def _cancel_all_timers(self):
        """Cancelar todos los timers/after pendientes"""
        for timer_attr in ('_reloj_after', '_monitor_turno_after',
                           '_turno_display_after', '_debounce_timer'):
            timer_id = getattr(self, timer_attr, None)
            if timer_id is not None:
                try:
                    self.after_cancel(timer_id)
                except Exception:
                    pass
                setattr(self, timer_attr, None)
