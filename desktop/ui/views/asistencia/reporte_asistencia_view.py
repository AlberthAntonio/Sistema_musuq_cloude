"""

Vista de Reporte de Asistencia Personal - ESTILO MEJORADO

Sistema Musuq Cloud

Dashboard con métricas KPI, búsqueda inteligente y scroll infinito

"""

import customtkinter as ctk
from tkinter import messagebox
import threading
import time
from datetime import date, timedelta
from tkcalendar import DateEntry

# --- CONTROLLER Y ESTILOS ---
from controllers.reporte_asistencia_controller import ReporteAsistenciaController
from styles import tabla_style as st
from core.theme_manager import ThemeManager as TM

# Intentamos importar reportlab para el PDF
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class ReporteAsistenciaView(ctk.CTkFrame):
    """Vista de Dashboard de Asistencia Personal con diseño profesional"""

    def __init__(self, parent, auth_client=None):
        super().__init__(parent, fg_color="transparent")
        self.controller = ReporteAsistenciaController()
        self.alumno_seleccionado_id = None
        self.datos_actuales = None
        self.search_job = None
        self.last_req_time = 0

        # Anchos de columnas: [Fecha, Día, Hora, Estado, Turno, Observación]
        self.ANCHOS_COLUMNAS = [110, 100, 100, 140, 100, 200]

        # Variables para scroll infinito
        self.historial_cache = []
        self.registros_cargados = 0
        self.lote_tamano = 20
        self.cargando_mas = False

        # Layout Principal: 2 Columnas (sidebar + dashboard)
        self.grid_columnconfigure(0, weight=0)  # Sidebar fijo
        self.grid_columnconfigure(1, weight=1)  # Dashboard expandible
        self.grid_rowconfigure(0, weight=1)

        self.create_widgets()

    def create_widgets(self):
        # ===========================================================
        # PANEL IZQUIERDO: SIDEBAR (Búsqueda + Perfil)
        # ============================================================
        self.panel_izq = ctk.CTkFrame(
            self,
            width=320,
            fg_color=TM.bg_card(),
            corner_radius=0
        )
        self.panel_izq.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        self.panel_izq.grid_propagate(False)

        # Título Lateral mejorado
        header_frame = ctk.CTkFrame(self.panel_izq, fg_color="transparent")
        header_frame.pack(pady=(20, 15), padx=15)

        ctk.CTkLabel(
            header_frame,
            text="📊 REPORTE DE",
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
            text_color=TM.text_secondary()
        ).pack()

        ctk.CTkLabel(
            header_frame,
            text="ASISTENCIA",
            font=ctk.CTkFont(family="Roboto", size=22, weight="bold"),
            text_color=TM.text()
        ).pack()

        # Separador
        ctk.CTkFrame(
            self.panel_izq,
            height=2,
            fg_color=TM.bg_panel()
        ).pack(fill="x", padx=20, pady=(0, 15))

        # --- Buscador Mejorado ---
        self.fr_search = ctk.CTkFrame(self.panel_izq, fg_color="transparent")
        self.fr_search.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            self.fr_search,
            text="Buscar Alumno",
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(anchor="w", pady=(0, 5))

        # Input mejorado (estilo consistente)
        self.search_box = ctk.CTkFrame(
            self.fr_search,
            fg_color=TM.bg_panel(),
            corner_radius=10,
            height=40
        )
        self.search_box.pack(fill="x")
        self.search_box.pack_propagate(False)

        ctk.CTkLabel(
            self.search_box,
            text="🔍",
            font=ctk.CTkFont(family="Arial", size=14),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(12, 5))

        self.ent_busqueda = ctk.CTkEntry(
            self.search_box,
            placeholder_text="Nombre o DNI...",
            border_width=0,
            fg_color="transparent",
            text_color=TM.text()
        )
        self.ent_busqueda.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.ent_busqueda.bind("<KeyRelease>", self.realizar_busqueda)

        # Lista de Resultados mejorada
        self.lista_resultados = ctk.CTkScrollableFrame(
            self.panel_izq,
            height=200,
            fg_color=TM.bg_panel(),
            corner_radius=10
        )
        self.lista_resultados.pack(pady=(10, 15), padx=15, fill="both", expand=True)

        # --- Tarjeta de Perfil Mejorada ---
        self.card_perfil = ctk.CTkFrame(
            self.panel_izq,
            fg_color=TM.bg_panel(),
            corner_radius=15
        )
        self.card_perfil.pack(pady=(0, 15), padx=15, fill="x")

        # Icono mejorado
        icon_container = ctk.CTkFrame(
            self.card_perfil,
            fg_color="transparent"
        )
        icon_container.pack(pady=(15, 5))

        ctk.CTkLabel(
            icon_container,
            text="👤",
            font=ctk.CTkFont(family="Arial", size=50)
        ).pack()

        # Nombre
        self.lbl_nombre = ctk.CTkLabel(
            self.card_perfil,
            text="--",
            font=ctk.CTkFont(family="Roboto", size=15, weight="bold"),
            text_color=TM.text(),
            wraplength=260
        )
        self.lbl_nombre.pack(pady=(0, 5), padx=15)

        # Información detallada
        self.info_grid = ctk.CTkFrame(self.card_perfil, fg_color="transparent")
        self.info_grid.pack(fill="x", pady=(5, 15), padx=15)

        self.lbl_codigo = ctk.CTkLabel(
            self.info_grid,
            text="COD: --",
            text_color=TM.text_secondary(),
            font=ctk.CTkFont(family="Roboto", size=10)
        )
        self.lbl_codigo.pack()

        self.lbl_grupo = ctk.CTkLabel(
            self.info_grid,
            text="Grupo: --",
            text_color=TM.warning(),
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold")
        )
        self.lbl_grupo.pack(pady=(3, 0))

        # Botón PDF Mejorado
        self.btn_pdf = ctk.CTkButton(
            self.panel_izq,
            text="📄 DESCARGAR REPORTE",
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            fg_color=TM.danger(),
            hover_color="#c0392b",
            height=45,
            corner_radius=10,
            command=self.generar_pdf
        )
        self.btn_pdf.pack(fill="x", padx=15, pady=(0, 20))

        # ============================================================
        # PANEL DERECHO: DASHBOARD
        # ============================================================
        self.panel_der = ctk.CTkFrame(self, fg_color="transparent")
        self.panel_der.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)

        # --- Fila Superior: Filtros Mejorados ---
        self.fr_top = ctk.CTkFrame(
            self.panel_der,
            fg_color=TM.bg_card(),
            height=60,
            corner_radius=10
        )
        self.fr_top.pack(fill="x", pady=(0, 15))
        self.fr_top.pack_propagate(False)

        # Contenedor interno
        top_content = ctk.CTkFrame(self.fr_top, fg_color="transparent")
        top_content.pack(fill="both", expand=True, padx=20, pady=12)

        ctk.CTkLabel(
            top_content,
            text="📅 Rango de Análisis:",
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(0, 10))

        # DateEntries mejorados
        self.ent_desde = DateEntry(
            top_content,
            width=12,
            date_pattern='dd/mm/yyyy',
            background=TM.primary().lstrip('#'),  # Convertir a hex sin #
            foreground='white',
            borderwidth=0,
            font=("Roboto", 10)
        )
        self.ent_desde.pack(side="left", padx=5)
        self.ent_desde.set_date(date.today() - timedelta(days=30))

        ctk.CTkLabel(
            top_content,
            text="➡",
            text_color=TM.text_secondary(),
            font=ctk.CTkFont(family="Roboto", size=14)
        ).pack(side="left", padx=5)

        self.ent_hasta = DateEntry(
            top_content,
            width=12,
            date_pattern='dd/mm/yyyy',
            background=TM.primary().lstrip('#'),
            foreground='white',
            borderwidth=0,
            font=("Roboto", 10)
        )
        self.ent_hasta.pack(side="left", padx=5)

        self.btn_actualizar = ctk.CTkButton(
            top_content,
            text="🔄 ACTUALIZAR",
            width=140,
            height=36,
            fg_color="#404040",
            hover_color="#505050",
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            command=self.cargar_datos_alumno
        )
        self.btn_actualizar.pack(side="left", padx=15)

        # --- Tarjetas de Métricas KPI (Mejoradas) ---
        self.metrics_container = ctk.CTkFrame(self.panel_der, fg_color="transparent")
        self.metrics_container.pack(fill="x", pady=(0, 15))
        self.metrics_container.columnconfigure((0, 1, 2, 3), weight=1)

        # Inicializar con valores 0
        self.crear_tarjeta_metrica(0, "PUNTUALES", "0", "⏰", st.Colors.PUNTUAL)
        self.crear_tarjeta_metrica(1, "TARDANZAS", "0", "⏳", st.Colors.TARDANZA)
        self.crear_tarjeta_metrica(2, "FALTAS", "0", "❌", st.Colors.FALTA)
        self.crear_tarjeta_metrica(3, "% EFECTIVIDAD", "0%", "📈", st.Colors.ASISTENCIA, is_progress=True)

        # --- TABLA DE ASISTENCIA Mejorada ---
        self.container_tabla = ctk.CTkFrame(
            self.panel_der,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.container_tabla.pack(fill="both", expand=True)

        # Cabecera
        self.crear_cabecera_tabla()

        # Cuerpo scrollable
        self.scroll_tabla = ctk.CTkScrollableFrame(
            self.container_tabla,
            fg_color="transparent"
        )
        self.scroll_tabla.pack(fill="both", expand=True, padx=5, pady=5)
        self.scroll_tabla._parent_canvas.configure(yscrollcommand=self._hook_scroll)

        # Estado vacío mejorado
        self.empty_state = ctk.CTkFrame(self.scroll_tabla, fg_color="transparent")
        self.empty_state.pack(fill="both", expand=True, pady=80)

        ctk.CTkLabel(
            self.empty_state,
            text="📊",
            font=ctk.CTkFont(family="Arial", size=60)
        ).pack(pady=10)

        ctk.CTkLabel(
            self.empty_state,
            text="Seleccione un alumno",
            font=ctk.CTkFont(family="Roboto", size=18, weight="bold"),
            text_color=TM.text()
        ).pack()

        ctk.CTkLabel(
            self.empty_state,
            text="para ver su historial de asistencia",
            font=ctk.CTkFont(family="Roboto", size=13),
            text_color=TM.text_secondary()
        ).pack(pady=(5, 0))

        # Label cargando más
        self.lbl_cargando_mas = ctk.CTkLabel(
            self.scroll_tabla,
            text="⏳ Cargando más registros...",
            text_color=TM.primary(),
            font=ctk.CTkFont(family="Roboto", size=10, slant="italic")
        )

    # ============================================================
    # MÉTODOS VISUALES (Helpers)
    # ============================================================

    def crear_cabecera_tabla(self):
        """Crea la cabecera de la tabla con diseño mejorado"""
        header = ctk.CTkFrame(
            self.container_tabla,
            height=40,
            fg_color=st.Colors.TABLE_HEADER,
            corner_radius=5
        )
        header.pack(fill="x", padx=5, pady=(5, 0))

        cols = ["FECHA", "DÍA", "HORA", "ESTADO", "TURNO", "OBSERVACIÓN"]

        for i, col in enumerate(cols):
            ancho = self.ANCHOS_COLUMNAS[i]
            lbl = ctk.CTkLabel(
                header,
                text=col,
                font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
                text_color="white",
                width=ancho
            )
            lbl.pack(side="left", padx=2)

    def crear_tarjeta_metrica(self, col_index, titulo, valor, icono, color, is_progress=False):
        """Crea una tarjeta KPI con diseño mejorado"""
        # Card Container
        card = ctk.CTkFrame(
            self.metrics_container,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        card.grid(row=0, column=col_index, sticky="ew", padx=5)

        # Contenido
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", padx=20, pady=15)

        # Título
        ctk.CTkLabel(
            content,
            text=titulo,
            font=ctk.CTkFont(family="Roboto", size=10, weight="bold"),
            text_color=color
        ).pack(anchor="w")

        # Valor
        ctk.CTkLabel(
            content,
            text=valor,
            font=ctk.CTkFont(family="Roboto", size=28, weight="bold"),
            text_color=TM.text()
        ).pack(anchor="w", pady=(2, 5))

        # Icono de fondo
        ctk.CTkLabel(
            card,
            text=icono,
            font=ctk.CTkFont(family="Arial", size=40),
            text_color="#404040"
        ).place(relx=0.85, rely=0.5, anchor="center")

        # Barra de progreso o línea decorativa
        if is_progress:
            try:
                val_float = float(valor.replace("%", "")) / 100
            except:
                val_float = 0

            prog = ctk.CTkProgressBar(
                content,
                width=120,
                height=6,
                progress_color=color,
                fg_color=TM.bg_panel()
            )
            prog.pack(anchor="w", pady=5)
            prog.set(val_float)
        else:
            ctk.CTkFrame(
                content,
                height=3,
                width=40,
                fg_color=color,
                corner_radius=2
            ).pack(anchor="w", pady=5)

    def _hook_scroll(self, first, last):
        """Hook del scrollbar para scroll infinito"""
        try:
            self.scroll_tabla._scrollbar.set(first, last)
        except:
            pass

        if self.cargando_mas:
            return
        if not hasattr(self, 'historial_cache'):
            return
        if not self.historial_cache:
            return

        try:
            posicion_actual = float(last)

            if (posicion_actual >= 0.90 and
                    self.registros_cargados < len(self.historial_cache)):
                self.cargando_mas = True

                try:
                    if self.lbl_cargando_mas.winfo_exists():
                        self.lbl_cargando_mas.pack(pady=10)
                except:
                    pass

                self.after(200, self._renderizar_siguiente_lote)
        except Exception as e:
            if "bad window path" not in str(e):
                print(f"Error en _hook_scroll: {e}")
            self.cargando_mas = False

    # ============================================================
    # LÓGICA DEL CONTROLADOR (CON HILOS)
    # ============================================================

    def realizar_busqueda(self, event=None):
        """Búsqueda con debounce optimizado"""
        texto = self.ent_busqueda.get()

        if self.search_job:
            self.after_cancel(self.search_job)

        if len(texto) >= 2:
            self.search_job = self.after(500, lambda: self._iniciar_busqueda_thread(texto))
        elif len(texto) == 0:
            self._actualizar_lista_busqueda([], time.time())

    def _iniciar_busqueda_thread(self, texto):
        """Inicia el hilo de búsqueda"""
        timestamp = time.time()
        self.last_req_time = timestamp
        threading.Thread(
            target=self._busqueda_en_hilo,
            args=(texto, timestamp),
            daemon=True
        ).start()

    def _busqueda_en_hilo(self, texto, req_timestamp):
        """Búsqueda en segundo plano"""
        try:
            resultados = self.controller.buscar_alumnos(texto)
        except Exception as e:
            print(f"[ERROR BUSQUEDA]: {e}")
            resultados = []

        self.after(0, lambda: self._actualizar_lista_busqueda(resultados, req_timestamp))

    def _actualizar_lista_busqueda(self, resultados, req_timestamp):
        """Actualiza la UI con resultados de búsqueda"""
        if req_timestamp < self.last_req_time:
            return

        for widget in self.lista_resultados.winfo_children():
            widget.destroy()

        if not resultados:
            lbl = ctk.CTkLabel(
                self.lista_resultados,
                text="Sin resultados",
                text_color=TM.text_secondary()
            )
            lbl.pack(pady=10)
            return

        for alu in resultados:
            if alu.nombre_completo:
                name_alumno = alu.nombre_completo.replace(",", "").upper()
            else:
                name_alumno = f"{alu.apell_paterno} {alu.nombres}".upper()

            btn = ctk.CTkButton(
                self.lista_resultados,
                text=f"👤 {name_alumno}\n    {alu.dni}",
                fg_color="transparent",
                hover_color=st.Colors.HOVER,
                border_width=0,
                text_color=TM.text(),
                anchor="w",
                height=45,
                font=ctk.CTkFont(family="Roboto", size=11),
                command=lambda id=alu.id: self.seleccionar_alumno(id)
            )
            btn.pack(fill="x", pady=1, padx=5)

            # Separador sutil
            ctk.CTkFrame(
                self.lista_resultados,
                height=1,
                fg_color=TM.bg_panel()
            ).pack(fill="x", padx=5)

    def seleccionar_alumno(self, alumno_id):
        """Selecciona un alumno y carga sus datos"""
        self.alumno_seleccionado_id = alumno_id
        self.cargar_datos_alumno()

    def cargar_datos_alumno(self):
        """Inicia la carga de datos del alumno en un hilo"""
        if not self.alumno_seleccionado_id:
            return

        self.btn_actualizar.configure(state="disabled", text="Cargando...")

        f_ini = self.ent_desde.get()
        f_fin = self.ent_hasta.get()

        threading.Thread(
            target=self._cargar_datos_en_hilo,
            args=(self.alumno_seleccionado_id, f_ini, f_fin),
            daemon=True
        ).start()

    def _cargar_datos_en_hilo(self, id_alumno, f_ini, f_fin):
        """Consulta en segundo plano"""
        exito, msg, datos = self.controller.obtener_perfil_completo(id_alumno, f_ini, f_fin)
        self.after(0, lambda: self._actualizar_dashboard(exito, msg, datos))

    def _actualizar_dashboard(self, exito, msg, datos):
        """Actualiza todo el dashboard con los datos"""
        self.btn_actualizar.configure(state="normal", text="🔄 ACTUALIZAR")

        if not exito:
            messagebox.showerror("Error", msg)
            return

        self.scroll_tabla._parent_canvas.yview_moveto(0.0)
        self.lista_resultados._parent_canvas.yview_moveto(0.0)

        self.datos_actuales = datos

        # 1. Actualizar Perfil
        alu = datos["alumno"]
        self.lbl_nombre.configure(
            text=f"{alu.nombres.upper()}\n{alu.apell_paterno.upper()} {alu.apell_materno.upper()}"
        )
        self.lbl_codigo.configure(
            text=f"DNI: {alu.dni} | COD: {alu.codigo_matricula.upper()}"
        )
        self.lbl_grupo.configure(
            text=f"GRUPO: {(alu.grupo or '-').upper()} | HORARIO: {(alu.horario or '-').upper()}"
        )

        # 2. Actualizar KPIs
        stats = datos["stats"]
        for widget in self.metrics_container.winfo_children():
            widget.destroy()

        self.crear_tarjeta_metrica(0, "PUNTUALES", str(stats["puntual"]), "⏰", st.Colors.PUNTUAL)
        self.crear_tarjeta_metrica(1, "TARDANZAS", str(stats["tardanza"]), "⏳", st.Colors.TARDANZA)
        self.crear_tarjeta_metrica(2, "FALTAS", str(stats["falta"]), "❌", st.Colors.FALTA)
        self.crear_tarjeta_metrica(3, "% EFECTIVIDAD", f"{stats['efectividad']}%", "📈", st.Colors.ASISTENCIA, is_progress=True)

        # 3. Inicializar tabla con scroll infinito
        for widget in self.scroll_tabla.winfo_children():
            widget.destroy()

        self.historial_cache = datos["historial"]
        self.registros_cargados = 0
        self.cargando_mas = False

        if not datos["historial"]:
            self.empty_state.pack(fill="both", expand=True, pady=80)
            return

        self.empty_state.pack_forget()
        self._renderizar_siguiente_lote()

    def _renderizar_siguiente_lote(self):
        """Renderiza el siguiente grupo de registros"""
        inicio = self.registros_cargados
        fin = inicio + self.lote_tamano

        lote = self.historial_cache[inicio:fin]

        for item in lote:
            index_global = self.registros_cargados
            self._crear_fila_optimizada(item, index_global)
            self.registros_cargados += 1

        try:
            self.lbl_cargando_mas.pack_forget()
        except:
            pass

        self.cargando_mas = False
        print(f"📊 Historial: {self.registros_cargados}/{len(self.historial_cache)}")

    def _crear_fila_optimizada(self, fila, index):
        """Crea una fila optimizada con diseño mejorado"""
        # Colores mejorados (estilo consistente)
        bg_row = "#2d2d2d" if index % 2 == 0 else "#363636"

        # Lógica de estados
        # Backend devuelve: "Puntual", "Tarde", "Falta", "Justificado"
        estado = fila.get("estado", "")
        color_st = TM.text()
        icon = "❓"
        estado_u = estado.upper()

        if "PUNTUAL" in estado_u:
            color_st = st.Colors.PUNTUAL
            icon = "✅"
        elif "TARD" in estado_u:  # "Tarde" o "TARDANZA"
            color_st = st.Colors.TARDANZA
            icon = "⏳"
        elif "INASISTENCIA" in estado_u or "FALTA" in estado_u:
            color_st = st.Colors.FALTA
            icon = "❌"
        elif "JUSTIF" in estado_u:
            color_st = st.Colors.ASISTENCIA
            icon = "📄"

        # Crear Fila
        row = ctk.CTkFrame(
            self.scroll_tabla,
            fg_color=bg_row,
            corner_radius=5,
            height=38
        )
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        font_cell = ctk.CTkFont(family="Roboto", size=11)
        font_mono = ctk.CTkFont(family="Roboto Mono", size=11, weight="bold")

        # Celdas
        # 1. Fecha
        ctk.CTkLabel(
            row,
            text=fila.get("fecha", ""),
            text_color=TM.text(),
            font=font_mono,
            width=self.ANCHOS_COLUMNAS[0]
        ).pack(side="left", padx=2)

        # 2. Día — calculado desde "fecha", el backend no lo envía como campo
        fecha_str = fila.get("fecha", "")
        dia_str = ""
        try:
            from datetime import datetime as _dt
            dia_str = _dt.strptime(str(fecha_str), "%Y-%m-%d").strftime("%A").upper()[:3]
        except Exception:
            pass
        ctk.CTkLabel(
            row,
            text=dia_str,
            text_color=TM.text_secondary(),
            font=font_cell,
            width=self.ANCHOS_COLUMNAS[1]
        ).pack(side="left", padx=2)

        # 3. Hora
        ctk.CTkLabel(
            row,
            text=fila.get("hora", ""),
            text_color=TM.text(),
            font=font_mono,
            width=self.ANCHOS_COLUMNAS[2]
        ).pack(side="left", padx=2)

        # 4. Estado con icono
        f_st = ctk.CTkFrame(
            row,
            fg_color="transparent",
            width=self.ANCHOS_COLUMNAS[3],
            height=30
        )
        f_st.pack(side="left", padx=2)
        f_st.pack_propagate(False)

        ctk.CTkLabel(
            f_st,
            text=icon,
            font=ctk.CTkFont(family="Arial", size=13)
        ).pack(side="left", padx=(10, 5))

        ctk.CTkLabel(
            f_st,
            text=estado_u,
            text_color=color_st,
            font=ctk.CTkFont(family="Roboto", size=10, weight="bold")
        ).pack(side="left")

        # 5. Turno
        turno_txt = (fila.get("turno") or "-").upper()
        ctk.CTkLabel(
            row,
            text=turno_txt,
            text_color=TM.text_secondary(),
            font=font_cell,
            anchor="center",
            width=self.ANCHOS_COLUMNAS[4]
        ).pack(side="left", padx=2)

        # 6. Observación — el backend devuelve la clave como "observacion"
        obs_txt = (fila.get("observacion", "") or fila.get("obs", "")).upper()
        if len(obs_txt) > 35:
            obs_txt = obs_txt[:32] + "..."

        ctk.CTkLabel(
            row,
            text=obs_txt,
            text_color=TM.text_secondary(),
            font=font_cell,
            anchor="w",
            width=self.ANCHOS_COLUMNAS[5]
        ).pack(side="left", padx=2)

    # ============================================================
    # GENERACIÓN DE PDF
    # ============================================================

    def generar_pdf(self):
        """Genera reporte PDF o TXT"""
        if not self.datos_actuales:
            messagebox.showwarning(
                "Atención",
                "Primero seleccione un alumno y genere los datos."
            )
            return

        if not REPORTLAB_AVAILABLE:
            self._generar_reporte_texto()
            return

        try:
            alu = self.datos_actuales["alumno"]
            filename = f"Kardex_{alu.apell_paterno}_{date.today()}.pdf"

            c = canvas.Canvas(filename, pagesize=A4)
            width, height = A4

            # Header
            c.setFont("Helvetica-Bold", 16)
            c.drawString(
                50, height - 50,
                f"REPORTE DE ASISTENCIA: {alu.apell_paterno} {alu.nombres}"
            )

            c.setFont("Helvetica", 10)
            c.drawString(
                50, height - 70,
                f"Código: {alu.codigo_matricula} | DNI: {alu.dni}"
            )
            c.drawString(
                50, height - 85,
                f"Periodo: {self.ent_desde.get()} al {self.ent_hasta.get()}"
            )

            # Resumen
            stats = self.datos_actuales["stats"]
            resumen = f"Puntuales: {stats['puntual']} | Tardanzas: {stats['tardanza']} | Faltas: {stats['falta']} | Efectividad: {stats['efectividad']}%"

            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, height - 110, resumen)
            c.line(50, height - 120, width - 50, height - 120)

            # Tabla
            y = height - 140
            c.setFont("Helvetica-Bold", 9)
            c.drawString(50, y, "FECHA")
            c.drawString(120, y, "HORA")
            c.drawString(180, y, "ESTADO")
            c.drawString(300, y, "OBSERVACIÓN")

            y -= 20
            c.setFont("Helvetica", 9)

            for fila in self.datos_actuales["historial"]:
                if y < 50:
                    c.showPage()
                    y = height - 50

                c.drawString(50, y, str(fila["fecha"]))
                c.drawString(120, y, str(fila["hora"]))
                c.drawString(180, y, str(fila["estado"]))
                c.drawString(300, y, str(fila.get("obs", ""))[:40])
                y -= 15

            c.save()

            messagebox.showinfo(
                "PDF Generado",
                f"Se ha guardado el reporte exitosamente:\n{filename}"
            )

            import os
            os.startfile(filename)

        except Exception as e:
            messagebox.showerror("Error PDF", f"Hubo un error al crear el PDF: {e}")

    def _generar_reporte_texto(self):
        """Genera reporte en formato TXT"""
        try:
            alu = self.datos_actuales["alumno"]
            filename = f"Kardex_{alu.apell_paterno}_{date.today()}.txt"

            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"REPORTE DE ASISTENCIA: {alu.apell_paterno} {alu.nombres}\n")
                f.write("=" * 50 + "\n")

                for fila in self.datos_actuales["historial"]:
                    f.write(
                        f"{fila['fecha']} | {fila['hora']} | "
                        f"{fila['estado']} | {fila.get('obs', '')}\n"
                    )

            messagebox.showinfo(
                "TXT Generado",
                f"Se generó un archivo de texto simple:\n{filename}"
            )

            import os
            os.startfile(filename)

        except Exception as e:
            messagebox.showerror("Error TXT", f"Error: {e}")
