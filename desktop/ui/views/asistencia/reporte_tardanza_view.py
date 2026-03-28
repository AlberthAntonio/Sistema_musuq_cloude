"""
Vista de Reporte de Tardanzas - ESTILO PREMIUM MEJORADO
Sistema Musuq Cloud
Incluye: Navegación por fechas, Scroll infinito, WhatsApp, Exportar CSV
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import date, timedelta, datetime
import webbrowser
import urllib.parse
import threading
from tkcalendar import DateEntry

from controllers.reporte_tardanza_controller import ReporteTardanzaController
from styles import tabla_style as st
from core.theme_manager import ThemeManager as TM


class ReporteTardanzaView(ctk.CTkFrame):
    """
    Vista profesional para el reporte y gestión de tardanzas.
    Características: Navegación por fechas, scroll infinito, exportación CSV, WhatsApp
    """

    def __init__(self, parent, auth_client=None):
        super().__init__(parent, fg_color="transparent")
        self.controller = ReporteTardanzaController()

        # Variables de control
        self.cargando = False
        self.datos_por_fecha = {}  # {"12/01/2025": [lista_alumnos]}
        self.botones_fecha = {}  # {"12/01/2025": widget_boton}
        self.fecha_activa = None
        self.registros_cache_tab = []
        self.registros_cargados_tab = 0
        self.lote_tamano = 20  # Scroll infinito
        self.cargando_mas = False

        # Anchos de columna
        self.ANCHOS = [80, 250, 100, 80, 140, 130, 80]

        # Configuración Grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Tabla expandible

        self.create_widgets()

    def create_widgets(self):
        # ============================
        # 1. HEADER
        # ============================
        self.fr_header = ctk.CTkFrame(
            self,
            fg_color=TM.bg_card(),
            corner_radius=10,
            height=70
        )
        self.fr_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 15))
        self.fr_header.grid_propagate(False)

        header_content = ctk.CTkFrame(self.fr_header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=20, pady=15)

        # Título principal
        title_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        title_frame.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            title_frame,
            text="⏰ GESTIÓN DE TARDANZAS",
            font=ctk.CTkFont(family="Roboto", size=22, weight="bold"),
            text_color=TM.text()
        ).pack(side="left")

        # Indicador de carga
        self.lbl_loader = ctk.CTkLabel(
            title_frame,
            text="⏳ Procesando datos...",
            text_color=TM.warning(),
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold")
        )

        # ============================
        # 2. PANEL DE FILTROS (3 COLUMNAS)
        # ============================
        self.panel_filtros = ctk.CTkFrame(
            self,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.panel_filtros.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))
        self.panel_filtros.columnconfigure((0, 1, 2), weight=1)

        # --- COLUMNA 1: RANGO DE FECHAS ---
        self._crear_col_fechas()

        # --- COLUMNA 2: FILTROS ---
        self._crear_col_filtros()

        # --- COLUMNA 3: ACCIONES ---
        self._crear_col_acciones()

        # ============================
        # 3. BARRA DE NAVEGACIÓN POR FECHAS (TABS)
        # ============================
        self.fr_tabs_container = ctk.CTkFrame(
            self,
            fg_color=TM.bg_card(),
            corner_radius=10,
            height=60
        )
        self.fr_tabs_container.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 15))
        self.fr_tabs_container.grid_propagate(False)

        # Título de sección
        tabs_header = ctk.CTkFrame(self.fr_tabs_container, fg_color="transparent")
        tabs_header.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            tabs_header,
            text="📅 NAVEGACIÓN POR FECHAS",
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(side="left")

        # Scroll horizontal para pestañas
        self.fr_nav_fechas = ctk.CTkScrollableFrame(
            self.fr_tabs_container,
            orientation="horizontal",
            height=30,
            fg_color="transparent"
        )
        self.fr_nav_fechas.pack(fill="x", expand=True, padx=15, pady=(0, 10))

        # Mensaje inicial
        self.lbl_nav_info = ctk.CTkLabel(
            self.fr_nav_fechas,
            text="Seleccione un rango y busque para ver los días disponibles",
            text_color=TM.text_secondary(),
            font=ctk.CTkFont(family="Roboto", size=11)
        )
        self.lbl_nav_info.pack(padx=10, pady=5)

        # Contenedor de tabs (botones)
        self.fr_nav_tabs = ctk.CTkFrame(self.fr_nav_fechas, fg_color="transparent")
        self.fr_nav_tabs.pack_forget()

        # ============================
        # 4. TABLA DE RESULTADOS
        # ============================
        self.fr_tabla = ctk.CTkFrame(
            self,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.fr_tabla.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Cabecera
        self._crear_cabecera()

        # Cuerpo scrollable
        self.scroll_tabla = ctk.CTkScrollableFrame(
            self.fr_tabla,
            fg_color="transparent"
        )
        self.scroll_tabla.pack(fill="both", expand=True, padx=5, pady=5)

        # Hook del scroll para scroll infinito
        self.scroll_tabla._parent_canvas.configure(yscrollcommand=self._hook_scroll)

        # Mensaje inicial
        self.lbl_vacio = ctk.CTkLabel(
            self.scroll_tabla,
            text="\n🔍 Realice una búsqueda para ver resultados",
            font=ctk.CTkFont(family="Roboto", size=14),
            text_color=TM.text_secondary()
        )
        self.lbl_vacio.pack(pady=40)

        # Label de "cargando más"
        self.lbl_cargando_mas = ctk.CTkLabel(
            self.scroll_tabla,
            text="⏳ Cargando más registros...",
            text_color=TM.primary(),
            font=ctk.CTkFont(family="Roboto", size=10, slant="italic")
        )

    def _crear_col_fechas(self):
        """Columna 1: Rango de fechas"""
        f_fechas = ctk.CTkFrame(self.panel_filtros, fg_color="transparent")
        f_fechas.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        # Título
        ctk.CTkLabel(
            f_fechas,
            text="📅 Rango de Fechas",
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(anchor="w", pady=(0, 10))

        # Desde
        f_d = ctk.CTkFrame(f_fechas, fg_color="transparent")
        f_d.pack(fill="x", pady=3)

        ctk.CTkLabel(
            f_d,
            text="Desde:",
            width=60,
            anchor="w",
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(0, 5))

        self.ent_desde = DateEntry(
            f_d,
            width=12,
            background=TM.warning(),
            foreground='white',
            borderwidth=0,
            date_pattern='dd/mm/yyyy'
        )
        self.ent_desde.pack(side="left", padx=5)
        self.ent_desde.set_date(date.today() - timedelta(days=7))

        # Hasta
        f_h = ctk.CTkFrame(f_fechas, fg_color="transparent")
        f_h.pack(fill="x", pady=3)

        ctk.CTkLabel(
            f_h,
            text="Hasta:",
            width=60,
            anchor="w",
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(0, 5))

        self.ent_hasta = DateEntry(
            f_h,
            width=12,
            background=TM.warning(),
            foreground='white',
            borderwidth=0,
            date_pattern='dd/mm/yyyy'
        )
        self.ent_hasta.pack(side="left", padx=5)
        self.ent_hasta.set_date(date.today())

    def _crear_col_filtros(self):
        """Columna 2: Filtros adicionales"""
        f_filtros = ctk.CTkFrame(self.panel_filtros, fg_color="transparent")
        f_filtros.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

        # Título
        ctk.CTkLabel(
            f_filtros,
            text="🔍 Filtros Adicionales",
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(anchor="w", pady=(0, 10))

        # Grid interno para combos
        f_grid = ctk.CTkFrame(f_filtros, fg_color="transparent")
        f_grid.pack(fill="x")

        combo_style = {
            "fg_color": TM.bg_panel(),
            "border_width": 0,
            "button_color": TM.warning(),
            "button_hover_color": "#d35400",
            "dropdown_fg_color": TM.bg_panel(),
            "font": ctk.CTkFont(family="Roboto", size=11),
            "width": 140
        }

        # Horario
        ctk.CTkLabel(
            f_grid,
            text="Horario:",
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).grid(row=0, column=0, padx=(0, 10), pady=5, sticky="e")

        self.cb_horario = ctk.CTkComboBox(
            f_grid,
            values=["Todos", "MATUTINO", "VESPERTINO", "DOBLE HORARIO"],
            **combo_style
        )
        self.cb_horario.set("Todos")
        self.cb_horario.grid(row=0, column=1, pady=5, sticky="w")

        # Grupo
        ctk.CTkLabel(
            f_grid,
            text="Grupo:",
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).grid(row=1, column=0, padx=(0, 10), pady=5, sticky="e")

        self.cb_grupo = ctk.CTkComboBox(
            f_grid,
            values=["Todos", "A", "B", "C", "D"],
            **combo_style
        )
        self.cb_grupo.set("Todos")
        self.cb_grupo.grid(row=1, column=1, pady=5, sticky="w")

        # Modalidad
        ctk.CTkLabel(
            f_grid,
            text="Modalidad:",
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).grid(row=2, column=0, padx=(0, 10), pady=5, sticky="e")

        self.cb_modalidad = ctk.CTkComboBox(
            f_grid,
            values=["Todos", "ORDINARIO", "PRIMERA OPCION", "COLEGIO", "REFORZAMIENTO"],
            **combo_style
        )
        self.cb_modalidad.set("Todos")
        self.cb_modalidad.grid(row=2, column=1, pady=5, sticky="w")

    def _crear_col_acciones(self):
        """Columna 3: Acciones y estadísticas"""
        f_acciones = ctk.CTkFrame(self.panel_filtros, fg_color="transparent")
        f_acciones.grid(row=0, column=2, padx=15, pady=15, sticky="nsew")

        # Título
        ctk.CTkLabel(
            f_acciones,
            text="⚡ Acciones",
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(anchor="w", pady=(0, 10))

        # Botón Buscar
        self.btn_buscar = ctk.CTkButton(
            f_acciones,
            text="🔎 BUSCAR AHORA",
            fg_color=TM.primary(),
            hover_color="#2980b9",
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            command=self.iniciar_busqueda
        )
        self.btn_buscar.pack(fill="x", pady=(0, 8))

        # Botón Exportar CSV
        self.btn_exportar = ctk.CTkButton(
            f_acciones,
            text="📄 EXPORTAR CSV",
            fg_color=TM.warning(),
            hover_color="#d35400",
            height=38,
            corner_radius=10,
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            command=self.exportar_csv
        )
        self.btn_exportar.pack(fill="x")

    def _crear_cabecera(self):
        """Crear cabecera de tabla"""
        header = ctk.CTkFrame(
            self.fr_tabla,
            height=40,
            fg_color=st.Colors.TABLE_HEADER,
            corner_radius=5
        )
        header.pack(fill="x", padx=5, pady=(5, 0))

        titulos = ["CÓDIGO", "ALUMNO", "ESTADO", "HORARIO", "FECHA/HORA", "CELULAR", "CONTACTAR"]

        for i, t in enumerate(titulos):
            ctk.CTkLabel(
                header,
                text=t,
                font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
                text_color="white",
                width=self.ANCHOS[i]
            ).pack(side="left", padx=2)

    # ========================================================
    # LÓGICA DE BÚSQUEDA CON THREADING
    # ========================================================

    def iniciar_busqueda(self):
        """Iniciar búsqueda en hilo separado"""
        if self.cargando:
            return

        self.cargando = True
        self.lbl_loader.pack(side="left", padx=15)
        self.btn_buscar.configure(state="disabled", text="🔄 Buscando...")
        self.update_idletasks()

        # Limpiar tabla y tabs
        self._limpiar_tabla()
        self._limpiar_nav_tabs()

        # Parámetros
        params = {
            "inicio": self.ent_desde.get(),
            "fin": self.ent_hasta.get(),
            "horario": self.cb_horario.get(),
            "grupo": self.cb_grupo.get(),
            "modalidad": self.cb_modalidad.get()
        }

        # Resetear scroll
        self.scroll_tabla._parent_canvas.yview_moveto(0.0)

        # Iniciar thread
        threading.Thread(
            target=self._proceso_buscar_db,
            args=(params,),
            daemon=True
        ).start()

    def _proceso_buscar_db(self, params):
        """Proceso de búsqueda en base de datos"""
        try:
            # Obtener datos del rango
            exito, mensaje, datos_brutos = self.controller.filtrar_tardanzas(
                params["inicio"],
                params["fin"],
                params["horario"],
                params["grupo"],
                params["modalidad"]
            )

            # Agrupar por fecha si hay datos
            if exito and datos_brutos:
                agrupados = {}
                for d in datos_brutos:
                    # Extraer solo la fecha
                    fecha_str = str(d["fecha"]).split(" ")[0]
                    if fecha_str not in agrupados:
                        agrupados[fecha_str] = []
                    agrupados[fecha_str].append(d)

                # Ordenar fechas
                fechas_ordenadas = sorted(
                    agrupados.keys(),
                    key=lambda x: datetime.strptime(x, "%d/%m/%Y")
                )

                resultado = {
                    "datos_agrupados": agrupados,
                    "fechas_ordenadas": fechas_ordenadas
                }
            else:
                resultado = None

        except Exception as e:
            exito, mensaje, resultado = False, str(e), None

        # Volver al hilo principal
        self.after(0, lambda: self._configurar_navegacion(exito, mensaje, resultado))

    def _configurar_navegacion(self, exito, mensaje, resultado):
        """Configurar navegación por fechas (tabs)"""
        self.lbl_loader.pack_forget()
        self.btn_buscar.configure(state="normal", text="🔎 BUSCAR AHORA")
        self.cargando = False

        if not exito:
            messagebox.showerror("Error", mensaje)
            self._mostrar_estado_vacio("❌ Error al buscar datos")
            return

        if not resultado or not resultado["fechas_ordenadas"]:
            self._mostrar_estado_vacio("✅ No se encontraron tardanzas en este rango")
            self._mostrar_nav_info("Sin resultados")
            return

        # Guardar datos
        self.datos_por_fecha = resultado["datos_agrupados"]
        fechas = resultado["fechas_ordenadas"]
        self.botones_fecha = {}

        self._mostrar_nav_tabs()

        # Crear botones de pestañas
        for fecha in fechas:
            cant = len(self.datos_por_fecha[fecha])
            texto_btn = f"{fecha}\n({cant})"

            btn = ctk.CTkButton(
            self.fr_nav_tabs,
                text=texto_btn,
                width=100,
                height=40,
                fg_color="transparent",
                border_width=1,
                border_color="#404040",
                text_color=TM.text_secondary(),
                corner_radius=8,
                font=ctk.CTkFont(family="Roboto", size=10),
                command=lambda f=fecha: self.mostrar_dia_especifico(f)
            )
            btn.pack(side="left", padx=5, pady=2)
            self.botones_fecha[fecha] = btn

        # Seleccionar primera fecha automáticamente
        primera_fecha = fechas[0]
        self.mostrar_dia_especifico(primera_fecha)

    def mostrar_dia_especifico(self, fecha):
        """Mostrar registros de una fecha específica con scroll infinito"""
        # 1. Actualizar estilo de tabs
        if self.fecha_activa and self.fecha_activa in self.botones_fecha:
            self.botones_fecha[self.fecha_activa].configure(
                fg_color="transparent",
                border_color="#404040",
                text_color=TM.text_secondary()
            )

        self.fecha_activa = fecha
        self.botones_fecha[fecha].configure(
            fg_color=TM.warning(),
            border_color=TM.warning(),
            text_color="white"
        )

        # 2. Limpiar tabla
        self._limpiar_tabla()

        # 3. Resetear variables de scroll infinito
        self.registros_cache_tab = []
        self.registros_cargados_tab = 0
        self.cargando_mas = False

        # 4. Mostrar loader temporal
        lbl_loading = ctk.CTkLabel(
            self.scroll_tabla,
            text=f"⏳ Cargando registros del {fecha}...",
            text_color=TM.warning(),
            font=ctk.CTkFont(family="Roboto", size=14)
        )
        lbl_loading.pack(pady=30)

        # 5. Resetear scroll
        self.scroll_tabla._parent_canvas.yview_moveto(0.0)
        self.update_idletasks()

        # 6. Inicializar con scroll infinito
        self.after(250, lambda: self._inicializar_tab(fecha, lbl_loading))

    def _inicializar_tab(self, fecha, lbl_loading):
        """Inicializar tab con scroll infinito"""
        # Eliminar loader
        lbl_loading.destroy()

        # Obtener datos
        datos_dia = self.datos_por_fecha.get(fecha, [])

        if not datos_dia:
            self._mostrar_estado_vacio("📭 No hay registros para esta fecha")
            return

        # Guardar en cache
        self.registros_cache_tab = datos_dia
        self.registros_cargados_tab = 0
        self.cargando_mas = False

        # Cargar primer lote
        self._renderizar_siguiente_lote()

    def _renderizar_siguiente_lote(self):
        """Renderizar siguiente lote de registros (scroll infinito)"""
        inicio = self.registros_cargados_tab
        fin = inicio + self.lote_tamano

        # Extraer lote
        lote = self.registros_cache_tab[inicio:fin]

        # Renderizar cada registro
        for item in lote:
            index_global = self.registros_cargados_tab
            self._crear_fila(item, index_global)
            self.registros_cargados_tab += 1

        # Ocultar indicador
        try:
            self.lbl_cargando_mas.pack_forget()
        except:
            pass

        # Liberar lock
        self.cargando_mas = False

    def _hook_scroll(self, first, last):
        """Hook del scrollbar para detectar scroll infinito"""
        # 1. Actualizar scrollbar
        try:
            self.scroll_tabla._scrollbar.set(first, last)
        except:
            pass

        # 2. Validaciones
        if self.cargando_mas or not self.registros_cache_tab:
            return

        # 3. Detectar si llegamos al 90%
        try:
            posicion = float(last)
            if (posicion >= 0.90 and
                self.registros_cargados_tab < len(self.registros_cache_tab)):

                self.cargando_mas = True

                # Mostrar indicador
                try:
                    if self.lbl_cargando_mas.winfo_exists():
                        self.lbl_cargando_mas.pack(pady=10)
                except:
                    pass

                # Cargar siguiente lote
                self.after(200, self._renderizar_siguiente_lote)

        except Exception as e:
            if "bad window path" not in str(e):
                print(f"Error en scroll: {e}")
            self.cargando_mas = False

    # ========================================================
    # CREACIÓN DE FILAS
    # ========================================================

    def _crear_fila(self, d, index):
        """Crear fila en tabla con diseño mejorado"""
        # Colores alternados
        bg = "#2d2d2d" if index % 2 == 0 else "#363636"

        row = ctk.CTkFrame(
            self.scroll_tabla,
            fg_color=bg,
            corner_radius=5,
            height=38
        )
        row.pack(fill="x", pady=1)
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

        # 1. CÓDIGO
        lbl_codigo = ctk.CTkLabel(
            row,
            text=d["codigo"],
            width=self.ANCHOS[0],
            text_color=TM.text_secondary(),
            font=font_mono
        )
        lbl_codigo.pack(side="left", padx=2)
        lbl_codigo.bind("<Enter>", on_enter)
        lbl_codigo.bind("<Leave>", on_leave)

        # 2. ALUMNO
        lbl_nombre = ctk.CTkLabel(
            row,
            text=d["nombre"],
            width=self.ANCHOS[1],
            anchor="w",
            text_color=TM.text(),
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold")
        )
        lbl_nombre.pack(side="left", padx=2)
        lbl_nombre.bind("<Enter>", on_enter)
        lbl_nombre.bind("<Leave>", on_leave)

        # 3. ESTADO (Badge)
        f_st = ctk.CTkFrame(
            row,
            fg_color="transparent",
            width=self.ANCHOS[2],
            height=38
        )
        f_st.pack(side="left", padx=2)
        f_st.pack_propagate(False)

        badge = ctk.CTkLabel(
            f_st,
            text="TARDANZA",
            fg_color=TM.warning(),
            text_color="white",
            corner_radius=5,
            width=80,
            height=22,
            font=ctk.CTkFont(family="Roboto", size=9, weight="bold")
        )
        badge.place(relx=0.5, rely=0.5, anchor="center")
        f_st.bind("<Enter>", on_enter)
        f_st.bind("<Leave>", on_leave)

        # 4. HORARIO
        lbl_turno = ctk.CTkLabel(
            row,
            text=d["horario"],
            width=self.ANCHOS[3],
            text_color=TM.text_secondary(),
            font=font_regular
        )
        lbl_turno.pack(side="left", padx=2)
        lbl_turno.bind("<Enter>", on_enter)
        lbl_turno.bind("<Leave>", on_leave)

        # 5. FECHA/HORA
        fecha_hora = f'{d["fecha"]} {d.get("hora", "")}'
        lbl_fecha = ctk.CTkLabel(
            row,
            text=fecha_hora.strip(),
            width=self.ANCHOS[4],
            text_color=TM.text(),
            font=font_mono
        )
        lbl_fecha.pack(side="left", padx=2)
        lbl_fecha.bind("<Enter>", on_enter)
        lbl_fecha.bind("<Leave>", on_leave)

        # 6. CELULAR
        lbl_cel = ctk.CTkLabel(
            row,
            text=d.get("celular", "Sin registro"),
            width=self.ANCHOS[5],
            text_color=TM.text_secondary(),
            font=font_regular
        )
        lbl_cel.pack(side="left", padx=2)
        lbl_cel.bind("<Enter>", on_enter)
        lbl_cel.bind("<Leave>", on_leave)

        # 7. BOTÓN WHATSAPP
        f_wa = ctk.CTkFrame(
            row,
            fg_color="transparent",
            width=self.ANCHOS[6],
            height=38
        )
        f_wa.pack(side="left", padx=2)
        f_wa.pack_propagate(False)

        btn_wa = ctk.CTkButton(
            f_wa,
            text="📲",
            width=35,
            height=28,
            fg_color=TM.success(),
            hover_color="#27ae60",
            corner_radius=5,
            font=ctk.CTkFont(family="Arial", size=14),
            command=lambda: self.enviar_whatsapp(
                d.get("celular", ""),
                d["nombre"],
                d["fecha"]
            )
        )
        btn_wa.place(relx=0.5, rely=0.5, anchor="center")

    def _mostrar_estado_vacio(self, mensaje):
        """Mostrar estado vacío elegante"""
        self._limpiar_tabla()
        self.lbl_vacio.configure(text=f"\n{mensaje}")
        self.lbl_vacio.pack(pady=40)

    def _limpiar_tabla(self):
        """Limpia solo los items de la tabla."""
        for w in self.scroll_tabla.winfo_children():
            if w in (self.lbl_vacio, self.lbl_cargando_mas):
                continue
            w.destroy()
        self.lbl_vacio.pack_forget()
        try:
            self.lbl_cargando_mas.pack_forget()
        except Exception:
            pass

    def _limpiar_nav_tabs(self):
        """Limpia tabs y muestra info por defecto."""
        for w in self.fr_nav_tabs.winfo_children():
            w.destroy()
        self.fr_nav_tabs.pack_forget()
        self.lbl_nav_info.configure(
            text="Seleccione un rango y busque para ver los días disponibles"
        )
        self.lbl_nav_info.pack(padx=10, pady=5)

    def _mostrar_nav_info(self, texto):
        """Muestra un mensaje informativo en la barra de navegación."""
        self.fr_nav_tabs.pack_forget()
        self.lbl_nav_info.configure(text=texto)
        self.lbl_nav_info.pack(padx=10, pady=5)

    def _mostrar_nav_tabs(self):
        """Muestra el contenedor de tabs y oculta el mensaje."""
        self.lbl_nav_info.pack_forget()
        self.fr_nav_tabs.pack(side="left")

    # ========================================================
    # FUNCIONALIDADES ADICIONALES
    # ========================================================

    def enviar_whatsapp(self, celular_raw, nombre, fecha):
        """Enviar mensaje de WhatsApp"""
        if not celular_raw or celular_raw == "None" or celular_raw == "Sin registro":
            messagebox.showwarning(
                "Atención",
                f"No hay número de celular registrado para {nombre}"
            )
            return

        # Limpiar celular
        celular = str(celular_raw).split("/")[0].strip().replace(" ", "")

        if len(celular) < 9:
            messagebox.showwarning("Error", "Número de celular inválido")
            return

        # Crear mensaje
        mensaje = (
            f"Estimado padre de familia, le informamos que su hijo(a) "
            f"*{nombre}* registró una TARDANZA el día {fecha}. "
            f"\n\nAtentamente,\nLa Dirección"
        )

        try:
            url = f"https://wa.me/51{celular}?text={urllib.parse.quote(mensaje)}"
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir WhatsApp: {e}")

    def exportar_csv(self):
        """Exportar resultados a CSV"""
        # Obtener todos los datos del rango actual
        params = {
            "inicio": self.ent_desde.get(),
            "fin": self.ent_hasta.get(),
            "horario": self.cb_horario.get(),
            "grupo": self.cb_grupo.get(),
            "modalidad": self.cb_modalidad.get()
        }

        try:
            exito, msg, datos = self.controller.filtrar_tardanzas(
                params["inicio"],
                params["fin"],
                params["horario"],
                params["grupo"],
                params["modalidad"]
            )

            if not datos:
                messagebox.showwarning("Vacío", "No hay datos para exportar")
                return

            # Generar archivo CSV
            filename = f"Reporte_Tardanzas_{date.today().strftime('%Y%m%d')}.csv"

            with open(filename, "w", encoding="utf-8") as f:
                # Encabezado
                f.write("CODIGO,ALUMNO,ESTADO,HORARIO,FECHA,HORA,CELULAR\n")

                # Datos
                for d in datos:
                    row = [
                        d.get("codigo", ""),
                        d.get("nombre", ""),
                        "TARDANZA",
                        d.get("horario", ""),
                        d.get("fecha", ""),
                        d.get("hora", ""),
                        d.get("celular", "")
                    ]
                    f.write(",".join(map(str, row)) + "\n")

            messagebox.showinfo(
                "✅ Exportado",
                f"Se generó el archivo:\n{filename}\n\nTotal de registros: {len(datos)}"
            )

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el archivo: {e}")
