"""
Vista de Control de Inasistencias - ESTILO PREMIUM MEJORADO
Sistema Musuq Cloud
Control diario de inasistencias con KPIs, filtros y scroll infinito
"""

import customtkinter as ctk
from tkinter import messagebox
import webbrowser
import urllib.parse
from datetime import date
import threading

from tkcalendar import DateEntry
from controllers.reporte_inasistencia_controller import ReporteInasistenciaController
from styles import tabla_style as st
from core.theme_manager import ThemeManager as TM
from mixins.infinite_scroll_mixin import InfiniteScrollMixin


class ReporteInasistenciaView(ctk.CTkFrame, InfiniteScrollMixin):
    """
    Vista profesional para control diario de inasistencias.
    Características: KPIs en tiempo real, scroll infinito, WhatsApp, justificación rápida
    """

    def __init__(self, master, auth_client=None):
        super().__init__(master, fg_color="transparent")
        self.auth_client = auth_client
        self.controller = ReporteInasistenciaController()

        # Configuración de anchos
        self.ANCHOS = [100, 250, 80, 100, 120, 100, 100]

        # Variables de estado
        self.cargando = False

        self.create_widgets()

        # Carga inicial
        self.after(500, self.iniciar_busqueda_thread)

    def create_widgets(self):
        # ============================
        # 1. HEADER PREMIUM
        # ============================
        self.fr_header = ctk.CTkFrame(
            self,
            fg_color=TM.bg_card(),
            corner_radius=10,
            height=70
        )
        self.fr_header.pack(fill="x", padx=20, pady=(20, 15))
        self.fr_header.pack_propagate(False)

        header_content = ctk.CTkFrame(self.fr_header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=20, pady=15)

        # Título
        title_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        title_frame.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            title_frame,
            text="🚨 CONTROL DIARIO DE INASISTENCIAS",
            font=ctk.CTkFont(family="Roboto", size=22, weight="bold"),
            text_color=TM.text()
        ).pack(side="left")

        # Indicador de carga
        self.lbl_loader = ctk.CTkLabel(
            title_frame,
            text="⏳ Cargando datos...",
            text_color=TM.warning(),
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold")
        )

        # ============================
        # 2. PANEL FECHA + KPIs
        # ============================
        self.fr_top = ctk.CTkFrame(self, fg_color="transparent")
        self.fr_top.pack(fill="x", padx=20, pady=(0, 15))

        # --- Selector de Fecha (Izquierda) ---
        self._crear_selector_fecha()

        # --- KPIs (Derecha) ---
        self._crear_kpis()

        # ============================
        # 3. BARRA DE FILTROS
        # ============================
        self._crear_barra_filtros()

        # ============================
        # 4. TABLA CON SCROLL INFINITO
        # ============================
        self.container_tabla = ctk.CTkFrame(
            self,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.container_tabla.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Cabecera
        self._crear_cabecera()

        # Cuerpo scrollable
        self.scroll_tabla = ctk.CTkScrollableFrame(
            self.container_tabla,
            fg_color="transparent"
        )
        self.scroll_tabla.pack(fill="both", expand=True, padx=5, pady=5)

        # Inicializar scroll infinito
        self.init_infinite_scroll(self.scroll_tabla, lote_tamano=20)

        # Estado vacío (estatico)
        self.empty_state_frame = ctk.CTkFrame(self.container_tabla, fg_color="transparent")
        self.empty_state_frame.pack_forget()

        self.empty_state_icon = ctk.CTkLabel(
            self.empty_state_frame,
            text="📭",
            font=ctk.CTkFont(family="Arial", size=60)
        )
        self.empty_state_icon.pack(pady=10)

        self.empty_state_title = ctk.CTkLabel(
            self.empty_state_frame,
            text="🔍 No hay inasistencias para mostrar",
            font=ctk.CTkFont(family="Roboto", size=16, weight="bold"),
            text_color=TM.text()
        )
        self.empty_state_title.pack()

        self.empty_state_subtitle = ctk.CTkLabel(
            self.empty_state_frame,
            text="Ajuste los filtros e intente nuevamente",
            font=ctk.CTkFont(family="Roboto", size=12),
            text_color=TM.text_secondary()
        )
        self.empty_state_subtitle.pack(pady=(5, 0))

    def _crear_selector_fecha(self):
        """Crear selector de fecha con diseño premium"""
        self.fr_fecha = ctk.CTkFrame(
            self.fr_top,
            fg_color=TM.bg_card(),
            corner_radius=10,
            width=200
        )
        self.fr_fecha.pack(side="left", padx=(0, 15), fill="y")
        self.fr_fecha.pack_propagate(False)

        # Contenedor interno
        fecha_content = ctk.CTkFrame(self.fr_fecha, fg_color="transparent")
        fecha_content.pack(fill="both", expand=True, padx=15, pady=15)

        # Icono
        ctk.CTkLabel(
            fecha_content,
            text="📅",
            font=ctk.CTkFont(family="Arial", size=40)
        ).pack(pady=(0, 5))

        # Título
        ctk.CTkLabel(
            fecha_content,
            text="FECHA DEL REPORTE",
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(pady=(0, 10))

        # Date Entry
        self.ent_fecha = DateEntry(
            fecha_content,
            width=12,
            background=TM.danger(),
            foreground='white',
            borderwidth=0,
            date_pattern='dd/mm/yyyy',
            font=("Roboto", 12, "bold")
        )
        self.ent_fecha.pack()
        self.ent_fecha.set_date(date.today())

    def _crear_kpis(self):
        """Crear tarjetas KPI con diseño premium"""
        self.fr_kpis = ctk.CTkFrame(self.fr_top, fg_color="transparent")
        self.fr_kpis.pack(side="left", fill="both", expand=True)
        self.fr_kpis.columnconfigure((0, 1, 2), weight=1)

        self.kpi_value_labels = {}

        kpis_data = [
            {
                "key": "total",
                "titulo": "TOTAL AUSENTES",
                "icono": "🚫",
                "color": TM.text_secondary()
            },
            {
                "key": "injustificadas",
                "titulo": "SIN JUSTIFICAR",
                "icono": "🔥",
                "color": TM.danger()
            },
            {
                "key": "justificadas",
                "titulo": "JUSTIFICADOS",
                "icono": "✅",
                "color": TM.success()
            }
        ]

        for i, kpi in enumerate(kpis_data):
            card = ctk.CTkFrame(
                self.fr_kpis,
                fg_color=TM.bg_card(),
                corner_radius=10
            )
            card.grid(row=0, column=i, padx=5, pady=0, sticky="nsew")

            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=15, pady=15)

            header = ctk.CTkFrame(content, fg_color="transparent")
            header.pack(fill="x")

            ctk.CTkLabel(
                header,
                text=kpi["icono"],
                font=ctk.CTkFont(family="Arial", size=40),
                text_color="#404040"
            ).pack(side="right")

            ctk.CTkLabel(
                header,
                text=kpi["titulo"],
                font=ctk.CTkFont(family="Roboto", size=10, weight="bold"),
                text_color=kpi["color"],
                anchor="w"
            ).pack(side="left", fill="x", expand=True)

            value_lbl = ctk.CTkLabel(
                content,
                text="0",
                font=ctk.CTkFont(family="Roboto", size=32, weight="bold"),
                text_color=TM.text(),
                anchor="w"
            )
            value_lbl.pack(fill="x", pady=(5, 0))
            self.kpi_value_labels[kpi["key"]] = value_lbl

            ctk.CTkFrame(
                content,
                height=3,
                fg_color=kpi["color"],
                corner_radius=2
            ).pack(fill="x", pady=(10, 0))

        # Inicializar KPIs
        self._actualizar_kpis({"total": 0, "injustificadas": 0, "justificadas": 0})

    def _actualizar_kpis(self, stats):
        """Actualizar tarjetas KPI"""
        self.kpi_value_labels["total"].configure(text=str(stats.get("total", 0)))
        self.kpi_value_labels["injustificadas"].configure(
            text=str(stats.get("injustificadas", 0))
        )
        self.kpi_value_labels["justificadas"].configure(
            text=str(stats.get("justificadas", 0))
        )

    def _crear_barra_filtros(self):
        """Crear barra de filtros con diseño premium"""
        self.fr_filtros = ctk.CTkFrame(
            self,
            fg_color=TM.bg_card(),
            corner_radius=10,
            height=60
        )
        self.fr_filtros.pack(fill="x", padx=20, pady=(0, 15))
        self.fr_filtros.pack_propagate(False)

        # Contenedor interno
        filtros_content = ctk.CTkFrame(self.fr_filtros, fg_color="transparent")
        filtros_content.pack(fill="both", expand=True, padx=15, pady=10)

        # Label Filtros
        ctk.CTkLabel(
            filtros_content,
            text="🔍 Filtros:",
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(0, 15))

        # ComboBox Horario del alumno
        self.cb_turno = ctk.CTkComboBox(
            filtros_content,
            values=["Todos", "MATUTINO", "VESPERTINO", "DOBLE HORARIO"],
            width=150,
            fg_color=TM.bg_panel(),
            border_width=0,
            button_color=TM.danger(),
            button_hover_color="#c0392b",
            dropdown_fg_color=TM.bg_panel(),
            font=ctk.CTkFont(family="Roboto", size=11)
        )
        self.cb_turno.set("Todos")
        self.cb_turno.pack(side="left", padx=5)

        # ComboBox Grupo
        self.cb_grupo = ctk.CTkComboBox(
            filtros_content,
            values=["Todos", "A", "B", "C", "D"],
            width=100,
            fg_color=TM.bg_panel(),
            border_width=0,
            button_color=TM.danger(),
            button_hover_color="#c0392b",
            dropdown_fg_color=TM.bg_panel(),
            font=ctk.CTkFont(family="Roboto", size=11)
        )
        self.cb_grupo.set("Todos")
        self.cb_grupo.pack(side="left", padx=5)

        # Switch Solo Injustificadas
        self.var_solo_injust = ctk.BooleanVar(value=True)
        self.sw_filtro = ctk.CTkSwitch(
            filtros_content,
            text="🔴 Solo Injustificadas",
            variable=self.var_solo_injust,
            progress_color=TM.danger(),
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text(),
            command=self.iniciar_busqueda_thread
        )
        self.sw_filtro.pack(side="left", padx=20)

        # Botones (lado derecho)
        # Botón Imprimir
        self.btn_imprimir = ctk.CTkButton(
            filtros_content,
            text="🖨️ IMPRIMIR",
            width=130,
            height=38,
            fg_color=TM.danger(),
            hover_color="#c0392b",
            corner_radius=10,
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            command=self.imprimir_reporte
        )
        self.btn_imprimir.pack(side="right", padx=(5, 0))

        # Botón Actualizar
        self.btn_buscar = ctk.CTkButton(
            filtros_content,
            text="🔄 ACTUALIZAR",
            width=130,
            height=38,
            fg_color=TM.primary(),
            hover_color="#2980b9",
            corner_radius=10,
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            command=self.iniciar_busqueda_thread
        )
        self.btn_buscar.pack(side="right", padx=5)

    def _crear_cabecera(self):
        """Crear cabecera de tabla"""
        header = ctk.CTkFrame(
            self.container_tabla,
            height=40,
            fg_color=st.Colors.TABLE_HEADER,
            corner_radius=5
        )
        header.pack(fill="x", padx=5, pady=(5, 0))

        titulos = ["CÓDIGO", "ALUMNO", "HORARIO", "CELULAR", "ESTADO", "CONTACTAR", "ACCIÓN"]

        for i, t in enumerate(titulos):
            f_col = ctk.CTkFrame(
                header,
                fg_color="transparent",
                width=self.ANCHOS[i],
                height=40
            )
            f_col.pack(side="left", padx=0)
            f_col.pack_propagate(False)
            ctk.CTkLabel(
                f_col,
                text=t,
                font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
                text_color="white",
                anchor="center"
            ).place(relx=0.5, rely=0.5, anchor="center")

    # ========================================================
    # LÓGICA DE BÚSQUEDA CON THREADING
    # ========================================================

    def iniciar_busqueda_thread(self):
        """Iniciar búsqueda en hilo separado"""
        if self.cargando:
            return

        self.cargando = True

        # Feedback visual
        self.lbl_loader.pack(side="left", padx=15)
        self.btn_buscar.configure(state="disabled", text="🔄 Cargando...")
        self._mostrar_scroll_tabla()

        # Limpiar tabla
        self.limpiar_scroll()

        # Recoger filtros
        params = {
            "fecha": self.ent_fecha.get(),
            "horario": self.cb_turno.get(),
            "grupo": self.cb_grupo.get(),
            "solo_inj": self.var_solo_injust.get()
        }

        # Lanzar thread
        threading.Thread(
            target=self._proceso_busqueda,
            args=(params,),
            daemon=True
        ).start()

    def _proceso_busqueda(self, p):
        """Proceso de búsqueda en base de datos"""
        try:
            exito, msg, stats, datos = self.controller.obtener_inasistencias_dia(
                p["fecha"],
                p["horario"],
                p["grupo"],
                "Todos",
                p["solo_inj"]
            )
        except Exception as e:
            exito, msg, stats, datos = False, str(e), {}, []

        # Volver al hilo principal
        self.after(0, lambda: self._finalizar_busqueda(exito, msg, stats, datos))

    def _finalizar_busqueda(self, exito, msg, stats, datos):
        """Finalizar búsqueda y actualizar UI (Main Thread)"""
        self.cargando = False
        self.lbl_loader.pack_forget()
        self.btn_buscar.configure(state="normal", text="🔄 ACTUALIZAR")

        if not exito:
            messagebox.showerror("Error", msg)
            self._mostrar_estado_vacio("❌ Error al cargar datos")
            return

        # Actualizar KPIs
        self._actualizar_kpis(stats)

        # Validar datos
        if not datos:
            self._mostrar_estado_vacio("✅ No hay faltas registradas con estos filtros")
            return

        # Cargar datos con scroll infinito
        self._mostrar_scroll_tabla()
        self.cargar_datos_scroll(datos)

    def _mostrar_estado_vacio(self, mensaje):
        """Mostrar estado vacío elegante"""
        self.limpiar_scroll()
        self.empty_state_title.configure(text=mensaje)
        self._mostrar_empty_state()

    def _mostrar_empty_state(self):
        self.scroll_tabla.pack_forget()
        self.empty_state_frame.pack(fill="both", expand=True, padx=5, pady=40)

    def _mostrar_scroll_tabla(self):
        self.empty_state_frame.pack_forget()
        self.scroll_tabla.pack(fill="both", expand=True, padx=5, pady=5)

    # ========================================================
    # RENDERIZADO DE FILAS (SCROLL INFINITO)
    # ========================================================

    def render_fila_scroll(self, d, index):
        """Método requerido por InfiniteScrollMixin - Renderizar fila"""
        # Colores alternados
        bg = "#2d2d2d" if index % 2 == 0 else "#363636"

        row = ctk.CTkFrame(
            self._scroll_widget_inf,
            fg_color=bg,
            corner_radius=5,
            height=40
        )
        row.pack(fill="x", pady=1, padx=0)
        row.pack_propagate(False)

        # Hover effect
        def on_enter(e):
            row.configure(fg_color="#34495e")

        def on_leave(e):
            row.configure(fg_color=bg)

        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)

        font_regular = ctk.CTkFont(family="Roboto", size=11)
        font_mono = ctk.CTkFont(family="Roboto Mono", size=11, weight="bold")

        def _celda(ancho):
            """Crear celda con ancho fijo para alineación exacta"""
            f = ctk.CTkFrame(row, fg_color="transparent", width=ancho, height=40)
            f.pack(side="left", padx=0)
            f.pack_propagate(False)
            f.bind("<Enter>", on_enter)
            f.bind("<Leave>", on_leave)
            return f

        # 1. CÓDIGO
        f_cod = _celda(self.ANCHOS[0])
        lbl_codigo = ctk.CTkLabel(
            f_cod,
            text=d["codigo"],
            text_color=TM.text_secondary(),
            font=font_mono
        )
        lbl_codigo.place(relx=0.5, rely=0.5, anchor="center")
        lbl_codigo.bind("<Enter>", on_enter)
        lbl_codigo.bind("<Leave>", on_leave)

        # 2. ALUMNO (con indicador de reincidente)
        nom_txt = d["nombre"].upper()
        nom_col = TM.text()

        if d.get("reincidente", False):
            nom_txt = f"🔥 {nom_txt}"
            nom_col = TM.warning()

        f_nom = _celda(self.ANCHOS[1])
        lbl_nombre = ctk.CTkLabel(
            f_nom,
            text=nom_txt,
            anchor="w",
            text_color=nom_col,
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold")
        )
        lbl_nombre.place(x=6, rely=0.5, anchor="w")
        lbl_nombre.bind("<Enter>", on_enter)
        lbl_nombre.bind("<Leave>", on_leave)

        # 3. HORARIO
        f_hor = _celda(self.ANCHOS[2])
        lbl_turno = ctk.CTkLabel(
            f_hor,
            text=d["horario"].upper(),
            text_color=TM.text_secondary(),
            font=font_regular
        )
        lbl_turno.place(relx=0.5, rely=0.5, anchor="center")
        lbl_turno.bind("<Enter>", on_enter)
        lbl_turno.bind("<Leave>", on_leave)

        # 4. CELULAR
        f_cel = _celda(self.ANCHOS[3])
        lbl_cel = ctk.CTkLabel(
            f_cel,
            text=d["celular"],
            text_color=TM.text_secondary(),
            font=font_regular
        )
        lbl_cel.place(relx=0.5, rely=0.5, anchor="center")
        lbl_cel.bind("<Enter>", on_enter)
        lbl_cel.bind("<Leave>", on_leave)

        # 5. ESTADO (Badge) — controller devuelve "Falta" o "Justificado"
        st_txt = d["estado"]
        st_bg = TM.danger() if st_txt.upper() in ("INASISTENCIA", "FALTA") else "#5dade2"

        f_st = _celda(self.ANCHOS[4])
        badge = ctk.CTkLabel(
            f_st,
            text=st_txt.upper(),
            fg_color=st_bg,
            text_color="white",
            corner_radius=5,
            width=100,
            height=24,
            font=ctk.CTkFont(family="Roboto", size=9, weight="bold")
        )
        badge.place(relx=0.5, rely=0.5, anchor="center")

        # 6. BOTÓN WHATSAPP
        f_wa = _celda(self.ANCHOS[5])
        btn_wa = ctk.CTkButton(
            f_wa,
            text="📲",
            width=60,
            height=26,
            fg_color=TM.success(),
            hover_color="#27ae60",
            corner_radius=5,
            font=ctk.CTkFont(family="Arial", size=12),
            command=lambda: self.enviar_whatsapp(d["celular"], d["nombre"])
        )
        btn_wa.place(relx=0.5, rely=0.5, anchor="center")

        # 7. BOTÓN JUSTIFICAR / CHECK
        f_jus = _celda(self.ANCHOS[6])

        if st_txt.upper() in ("INASISTENCIA", "FALTA"):
            btn_jus = ctk.CTkButton(
                f_jus,
                text="📝",
                width=60,
                height=26,
                fg_color=TM.warning(),
                hover_color="#d35400",
                corner_radius=5,
                font=ctk.CTkFont(family="Arial", size=12),
                command=lambda: self.justificar_falta(
                    d["id_asistencia"],
                    d["nombre"]
                )
            )
            btn_jus.place(relx=0.5, rely=0.5, anchor="center")
        else:
            ctk.CTkLabel(
                f_jus,
                text="✔️",
                text_color=TM.success(),
                font=ctk.CTkFont(family="Arial", size=14)
            ).place(relx=0.5, rely=0.5, anchor="center")

    # ========================================================
    # FUNCIONALIDADES
    # ========================================================

    def enviar_whatsapp(self, celular, nombre):
        """Enviar mensaje de WhatsApp a apoderado"""
        if not celular or celular == "None":
            messagebox.showwarning(
                "Atención",
                f"No hay número de celular registrado para {nombre}"
            )
            return

        cel_clean = str(celular).split("/")[0].strip().replace(" ", "")

        if len(cel_clean) < 9:
            messagebox.showwarning("Error", "Número celular inválido")
            return

        # Crear mensaje
        mensaje = (
            f"Estimado apoderado, le informamos que el estudiante *{nombre}* "
            f"NO ASISTIÓ hoy a clases ({self.ent_fecha.get()}). "
            f"Favor de comunicarse con coordinación urgentemente."
        )

        try:
            url = f"https://wa.me/51{cel_clean}?text={urllib.parse.quote(mensaje)}"
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir WhatsApp: {e}")

    def justificar_falta(self, id_asistencia, nombre):
        """Justificar falta rápidamente"""
        # Dialog para ingresar motivo
        dialog = ctk.CTkInputDialog(
            text=f"Justificar falta de:\n{nombre}\n\nIngrese motivo:",
            title="Justificación Rápida"
        )

        motivo = dialog.get_input()

        if motivo:
            exito, msg = self.controller.justificar_rapida(id_asistencia, motivo)

            if exito:
                messagebox.showinfo("✅ Éxito", msg)
                self.iniciar_busqueda_thread()  # Recargar datos
            else:
                messagebox.showerror("❌ Error", msg)

    def imprimir_reporte(self):
        """Generar reporte PDF/CSV"""
        total = self.get_total_registros()  # Método del Mixin

        if not total:
            messagebox.showwarning("Atención", "No hay datos para exportar")
            return

        messagebox.showinfo(
            "🖨️ Imprimir",
            f"Generando reporte con {total} registros...\n\n"
            f"(Función de exportación en desarrollo)"
        )
