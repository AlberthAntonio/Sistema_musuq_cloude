"""
Vista de Deudores/Morosidad - ESTILO PREMIUM MEJORADO
Sistema Musuq Cloud
Reporte de alumnos con deuda pendiente con distribución de columnas optimizada
VERSIÓN CORREGIDA: KPI aparece correctamente en esquina superior derecha
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from customtkinter import CTkFont
import threading
import webbrowser
import os
import math
from datetime import datetime
from typing import List, Dict, Any

from controllers.pagos_controller import PagosController
from styles import tabla_style as st
from core.theme_manager import ThemeManager as TM

# --- IMPORTACIONES PARA PDF (REPORTLAB) ---
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class DeudoresView(ctk.CTkFrame):
    """
    Vista profesional para reporte de morosidad.
    Características: Filtros, KPI deuda total, tabla con paginación+scroll infinito
    Distribución de columnas optimizada para no saturar la vista
    """

    def __init__(self, parent, auth_client=None):
        super().__init__(parent, fg_color="transparent")

        if not auth_client:
            raise ValueError("auth_client es requerido para inicializar DeudoresView")

        self.auth_client = auth_client
        self.controller = PagosController(auth_client.token)

        # --- CONFIGURACIÓN HÍBRIDA (CEREBRO) ---
        self.data_total = []        # Base de datos completa en RAM
        self.data_pagina = []       # Los 100 de esta página

        # 1. Paginación (Macro)
        self.pag_actual = 1
        self.items_por_pag = 100
        self.total_pags = 1

        # 2. Scroll Infinito (Micro)
        self.items_visibles = 0
        self.lote_scroll = 25
        self.lock_carga = False

        # Selección
        self.seleccionado = None
        self.seleccionado_widget = None
        self.bg_anterior = None

        # ANCHOS DE COLUMNA OPTIMIZADOS - Distribución balanceada
        self.W_COL = {
            'num': 50,         # +10 (antes 40)
            'alumno': 280,     # +30 (antes 250) - Más espacio para nombres largos
            'modalidad': 120,  # +20 (antes 100)
            'contacto': 110,   # +10 (antes 100)
            'costo': 100,      # +20 (antes 80) - Mejor visualización de montos
            'pagado': 100,     # +20 (antes 80)
            'deuda': 100,      # +20 (antes 80)
            'estado': 130      # +10 (antes 120)
        }

        self.crear_ui()
        self.cargar_datos()

    def crear_ui(self):
        """Crear interfaz completa"""
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Header con filtros y KPI
        self._crear_header()

        # 2. Tabla
        self._crear_tabla()

        # 3. Footer con paginación y acciones
        self._crear_footer()

    # ========================================================
    # HEADER CON FILTROS Y KPI - CORRECCIÓN APLICADA ⭐
    # ========================================================

    def _crear_header(self):
        """Crear header con filtros y KPI de deuda total"""
        fr_top = ctk.CTkFrame(
            self,
            height=110,
            fg_color=TM.bg_panel(),
            corner_radius=10
        )
        fr_top.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        fr_top.pack_propagate(False)

        # Container interno
        header_content = ctk.CTkFrame(fr_top, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=20, pady=15)

        # ⭐ CORRECCIÓN: KPI A LA DERECHA PRIMERO (antes del contenido izquierdo)
        self._crear_kpi_deuda(header_content)

        # Lado izquierdo: Icono + Título + Filtros (después del KPI)
        left_side = ctk.CTkFrame(header_content, fg_color="transparent")
        left_side.pack(side="left", fill="y")

        # Icono + Título
        title_row = ctk.CTkFrame(left_side, fg_color="transparent")
        title_row.pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            title_row,
            text="📊",
            font=CTkFont(family="Arial", size=32)
        ).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            title_row,
            text="REPORTE DE MOROSIDAD",
            font=CTkFont(family="Roboto", size=18, weight="bold"),
            text_color=TM.text()
        ).pack(side="left")

        # Filtros
        self._crear_filtros(left_side)

    def _crear_filtros(self, parent):
        """Crear filtros de grupo y modalidad"""
        filtros_row = ctk.CTkFrame(parent, fg_color="transparent")
        filtros_row.pack(anchor="w")

        grupos, modalidades = self.controller.obtener_filtros_disponibles()

        # Filtro Grupo
        ctk.CTkLabel(
            filtros_row,
            text="Grupo:",
            text_color=TM.text_secondary(),
            font=CTkFont(family="Roboto", size=11, weight="bold")
        ).pack(side="left", padx=(0, 5))

        self.cb_grupo = ctk.CTkComboBox(
            filtros_row,
            values=["Todos"] + grupos,
            width=110,
            height=35,
            command=self.cargar_datos,
            fg_color=TM.bg_card(),
            text_color=TM.text(),
            dropdown_fg_color=TM.bg_panel(),
            button_color=TM.primary(),
            button_hover_color="#2980b9",
            border_width=1,
            border_color="#404040",
            font=CTkFont(family="Roboto", size=11)
        )
        self.cb_grupo.pack(side="left", padx=(0, 15))

        # Filtro Modalidad
        ctk.CTkLabel(
            filtros_row,
            text="Modalidad:",
            text_color=TM.text_secondary(),
            font=CTkFont(family="Roboto", size=11, weight="bold")
        ).pack(side="left", padx=(0, 5))

        self.cb_modalidad = ctk.CTkComboBox(
            filtros_row,
            values=["Todas"] + modalidades,
            width=150,
            height=35,
            command=self.cargar_datos,
            fg_color=TM.bg_card(),
            text_color=TM.text(),
            dropdown_fg_color=TM.bg_panel(),
            button_color=TM.primary(),
            button_hover_color="#2980b9",
            border_width=1,
            border_color="#404040",
            font=CTkFont(family="Roboto", size=11)
        )
        self.cb_modalidad.pack(side="left")

    def _crear_kpi_deuda(self, parent):
        """Crear KPI de deuda total - título arriba, icono y monto abajo"""
        kpi_card = ctk.CTkFrame(
            parent,
            fg_color=TM.danger(),
            corner_radius=10,
            border_width=2,
            border_color="#c0392b"
        )
        kpi_card.pack(side="right", padx=(15, 0))

        # Contenedor interno
        kpi_content = ctk.CTkFrame(kpi_card, fg_color="transparent")
        kpi_content.pack(padx=25, pady=10)

        # Texto superior: DEUDA TOTAL
        ctk.CTkLabel(
            kpi_content,
            text="DEUDA TOTAL",
            font=CTkFont(family="Roboto", size=11, weight="bold"),
            text_color="#ecf0f1"
        ).pack(pady=(0, 4))

        # Fila inferior: icono + monto
        bottom_row = ctk.CTkFrame(kpi_content, fg_color="transparent")
        bottom_row.pack()

        ctk.CTkLabel(
            bottom_row,
            text="🚨",
            font=CTkFont(family="Arial", size=24)
        ).pack(side="left", padx=(0, 6))

        self.lbl_total_deuda = ctk.CTkLabel(
            bottom_row,
            text="S/. 0.00",
            font=CTkFont(family="Roboto", size=22, weight="bold"),
            text_color="white"
        )
        self.lbl_total_deuda.pack(side="left")


    # ========================================================
    # TABLA CON DISTRIBUCIÓN OPTIMIZADA
    # ========================================================

    def _crear_tabla(self):
        """Crear tabla con header y cuerpo scrollable"""
        self.fr_tabla_bg = ctk.CTkFrame(
            self,
            fg_color=TM.bg_panel(),
            corner_radius=10
        )
        self.fr_tabla_bg.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)

        # Header tabla - Distribución optimizada
        self._crear_header_tabla()

        # Loading label
        self.lbl_loading = ctk.CTkLabel(
            self.fr_tabla_bg,
            text="⏳ Cargando datos...",
            text_color="#f39c12",
            font=CTkFont(family="Roboto", size=12, weight="bold")
        )

        # Cuerpo scrollable
        self.scroll_tabla = ctk.CTkScrollableFrame(
            self.fr_tabla_bg,
            fg_color="transparent"
        )
        self.scroll_tabla.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Hook scroll infinito
        self.scroll_tabla._parent_canvas.configure(yscrollcommand=self._evento_scroll)

    def _crear_header_tabla(self):
        """Crear header de tabla con columnas bien distribuidas"""
        h_frame = ctk.CTkFrame(
            self.fr_tabla_bg,
            height=45,
            fg_color=TM.primary(),
            corner_radius=8
        )
        h_frame.pack(fill="x", padx=8, pady=(8, 0))
        h_frame.pack_propagate(False)

        # Columnas con anchos optimizados
        columnas = [
            ("#", self.W_COL['num'], "center"),
            ("ALUMNO", self.W_COL['alumno'], "w"),
            ("MODALIDAD", self.W_COL['modalidad'], "center"),
            ("CONTACTO", self.W_COL['contacto'], "center"),
            ("COSTO", self.W_COL['costo'], "e"),
            ("PAGADO", self.W_COL['pagado'], "e"),
            ("DEUDA", self.W_COL['deuda'], "e"),
            ("ESTADO", self.W_COL['estado'], "center")
        ]

        for texto, ancho, ancla in columnas:
            ctk.CTkLabel(
                h_frame,
                text=texto,
                width=ancho,
                anchor=ancla,
                font=CTkFont(family="Roboto", size=11, weight="bold"),
                text_color="white"
            ).pack(side="left", padx=3)

    # ========================================================
    # FOOTER CON PAGINACIÓN Y ACCIONES
    # ========================================================

    def _crear_footer(self):
        """Crear footer con paginación y botones de acción"""
        fr_bottom = ctk.CTkFrame(self, fg_color="transparent", height=60)
        fr_bottom.grid(row=2, column=0, sticky="ew", padx=15, pady=(10, 15))
        fr_bottom.pack_propagate(False)

        # Botón Actualizar
        ctk.CTkButton(
            fr_bottom,
            text="🔄 Actualizar",
            command=self.cargar_datos,
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            width=120,
            height=38,
            corner_radius=8,
            font=CTkFont(family="Roboto", size=11, weight="bold")
        ).pack(side="left", padx=(0, 10))

        # Paginación (centro)
        self._crear_paginacion(fr_bottom)

        # Botones de acción (derecha)
        ctk.CTkButton(
            fr_bottom,
            text="🖨️ Imprimir",
            fg_color=TM.primary(),
            hover_color="#2980b9",
            command=self.imprimir_reporte,
            width=120,
            height=38,
            corner_radius=8,
            font=CTkFont(family="Roboto", size=11, weight="bold")
        ).pack(side="right", padx=(5, 0))

        ctk.CTkButton(
            fr_bottom,
            text="📱 WhatsApp",
            fg_color="#25D366",
            hover_color="#128C7E",
            command=self.enviar_whatsapp,
            width=130,
            height=38,
            corner_radius=8,
            font=CTkFont(family="Roboto", size=11, weight="bold")
        ).pack(side="right", padx=(0, 5))

    def _crear_paginacion(self, parent):
        """Crear controles de paginación"""
        fr_pag = ctk.CTkFrame(parent, fg_color="transparent")
        fr_pag.pack(side="left", expand=True)

        # Botón Anterior
        self.btn_ant = ctk.CTkButton(
            fr_pag,
            text="◀ Ant",
            width=80,
            height=38,
            fg_color=TM.bg_card(),
            hover_color="#404040",
            command=lambda: self.cambiar_pag(-1),
            corner_radius=8,
            font=CTkFont(family="Roboto", size=11, weight="bold")
        )
        self.btn_ant.pack(side="left", padx=(0, 10))

        # Label paginación
        self.lbl_pag = ctk.CTkLabel(
            fr_pag,
            text="Pag 1/1",
            font=CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text()
        )
        self.lbl_pag.pack(side="left", padx=15)

        # Botón Siguiente
        self.btn_sig = ctk.CTkButton(
            fr_pag,
            text="Sig ▶",
            width=80,
            height=38,
            fg_color=TM.bg_card(),
            hover_color="#404040",
            command=lambda: self.cambiar_pag(1),
            corner_radius=8,
            font=CTkFont(family="Roboto", size=11, weight="bold")
        )
        self.btn_sig.pack(side="left", padx=(10, 0))

    # ========================================================
    # LÓGICA DE CARGA DE DATOS
    # ========================================================

    def cargar_datos(self, event=None):
        """Cargar datos en segundo plano"""
        self.lbl_loading.pack(pady=20)
        self.btn_ant.configure(state="disabled")
        self.btn_sig.configure(state="disabled")

        for w in self.scroll_tabla.winfo_children():
            w.destroy()

        g = self.cb_grupo.get()
        m = self.cb_modalidad.get()

        threading.Thread(
            target=self._proceso_en_segundo_plano,
            args=(g, m),
            daemon=True
        ).start()

    def _proceso_en_segundo_plano(self, grupo, modalidad):
        """Proceso de carga en thread separado"""
        datos = self.controller.obtener_lista_deudores(grupo, modalidad)
        total = sum(d["deuda"] for d in datos)
        self.after(0, lambda: self._finalizar_carga(datos, total))

    def _finalizar_carga(self, datos, total):
        """Finalizar carga y renderizar datos"""
        self.lbl_loading.pack_forget()
        self.lbl_total_deuda.configure(text=f"S/. {total:,.2f}")

        self.data_total = datos

        if not datos:
            self.total_pags = 1
            self._mostrar_estado_vacio()
        else:
            self.total_pags = math.ceil(len(datos) / self.items_por_pag)
            self.pag_actual = 1
            self.renderizar_pagina()

    def _mostrar_estado_vacio(self):
        """Mostrar estado vacío cuando no hay datos"""
        empty = ctk.CTkFrame(self.scroll_tabla, fg_color="transparent")
        empty.pack(pady=60)

        ctk.CTkLabel(
            empty,
            text="📋",
            font=CTkFont(family="Arial", size=60)
        ).pack()

        ctk.CTkLabel(
            empty,
            text="No hay datos de morosidad",
            font=CTkFont(family="Roboto", size=14, weight="bold"),
            text_color=TM.text()
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            empty,
            text="No se encontraron alumnos con deuda según los filtros seleccionados",
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack()

    # ========================================================
    # PAGINACIÓN + SCROLL INFINITO
    # ========================================================

    def cambiar_pag(self, direccion):
        """Cambiar de página"""
        nuevo = self.pag_actual + direccion
        if 1 <= nuevo <= self.total_pags:
            self.pag_actual = nuevo
            self.renderizar_pagina()

    def renderizar_pagina(self):
        """Renderizar página actual"""
        for w in self.scroll_tabla.winfo_children():
            w.destroy()

        self.scroll_tabla._parent_canvas.yview_moveto(0.0)

        inicio = (self.pag_actual - 1) * self.items_por_pag
        fin = inicio + self.items_por_pag
        self.data_pagina = self.data_total[inicio:fin]

        self.items_visibles = 0
        self.lock_carga = False

        self.lbl_pag.configure(text=f"Pag {self.pag_actual}/{self.total_pags}")
        self.btn_ant.configure(state="normal" if self.pag_actual > 1 else "disabled")
        self.btn_sig.configure(state="normal" if self.pag_actual < self.total_pags else "disabled")

        self._pintar_lote_scroll()

    def _evento_scroll(self, first, last):
        """Detectar scroll para carga progresiva"""
        self.scroll_tabla._scrollbar.set(first, last)

        if self.lock_carga:
            return

        try:
            if float(last) > 0.90 and self.items_visibles < len(self.data_pagina):
                self.lock_carga = True
                self.after(10, self._pintar_lote_scroll)
        except:
            pass

    def _pintar_lote_scroll(self):
        """Pintar lote de filas (scroll infinito)"""
        inicio = self.items_visibles
        fin = inicio + self.lote_scroll
        sub_lote = self.data_pagina[inicio:fin]

        for i, d in enumerate(sub_lote):
            idx = (self.pag_actual - 1) * self.items_por_pag + inicio + i + 1
            self._crear_fila_visual(d, idx)

        self.items_visibles += len(sub_lote)
        self.lock_carga = False

    def _crear_fila_visual(self, d, index):
        """Crear fila visual con distribución optimizada de columnas"""
        bg = st.Colors.ROW_ODD if index % 2 == 0 else st.Colors.ROW_EVEN

        row = ctk.CTkFrame(
            self.scroll_tabla,
            fg_color=bg,
            corner_radius=6,
            height=40
        )
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)
        row.bind("<Button-1>", lambda e: self.seleccionar_fila(row, d))

        def add_cell(txt, ancho, color=None, anchor="center", bold=False):
            """Helper para crear celda"""
            if color is None:
                color = TM.text()

            weight = "bold" if bold else "normal"
            lbl = ctk.CTkLabel(
                row,
                text=str(txt),
                width=ancho,
                anchor=anchor,
                text_color=color,
                font=CTkFont(family="Roboto", size=11, weight=weight)
            )
            lbl.pack(side="left", padx=3)
            lbl.bind("<Button-1>", lambda e: self.seleccionar_fila(row, d))

        # Columnas con anchos optimizados
        add_cell(d['icono'], self.W_COL['num'])
        add_cell(d['nombre'], self.W_COL['alumno'], TM.text(), "w", True)
        add_cell(d['modalidad'], self.W_COL['modalidad'], "#95a5a6")
        add_cell(d['contacto'], self.W_COL['contacto'], "#bdc3c7")
        add_cell(f"S/. {d['costo']:.2f}", self.W_COL['costo'], "#7f8c8d", "e")
        add_cell(f"S/. {d['pagado']:.2f}", self.W_COL['pagado'], "#27ae60", "e", True)
        add_cell(f"S/. {d['deuda']:.2f}", self.W_COL['deuda'], "#e74c3c", "e", True)

        # Badge de estado
        col_badge = {
            "CRITICO": "#c0392b",
            "MEDIO": "#e67e22",
            "BAJO": "#27ae60"
        }.get(d.get('tag', 'BAJO'), "#27ae60")

        f_badge = ctk.CTkFrame(
            row,
            fg_color=col_badge,
            width=self.W_COL['estado'],
            height=28,
            corner_radius=14
        )
        f_badge.pack(side="left", padx=3)

        l_badge = ctk.CTkLabel(
            f_badge,
            text=d['estado_desc'],
            text_color="white",
            font=CTkFont(family="Roboto", size=10, weight="bold")
        )
        l_badge.place(relx=0.5, rely=0.5, anchor="center")

        f_badge.bind("<Button-1>", lambda e: self.seleccionar_fila(row, d))
        l_badge.bind("<Button-1>", lambda e: self.seleccionar_fila(row, d))

    def seleccionar_fila(self, widget, data):
        """Seleccionar fila"""
        if self.seleccionado_widget and self.seleccionado_widget.winfo_exists():
            try:
                self.seleccionado_widget.configure(fg_color=self.bg_anterior)
            except:
                pass

        self.seleccionado_widget = widget
        self.bg_anterior = widget.cget("fg_color")
        self.seleccionado = data
        widget.configure(fg_color="#34495e")

    # ========================================================
    # ACCIONES
    # ========================================================

    def enviar_whatsapp(self):
        """Enviar mensaje de WhatsApp al seleccionado"""
        if not self.seleccionado:
            messagebox.showwarning("Aviso", "Seleccione un alumno de la lista")
            return

        d = self.seleccionado
        if len(str(d['contacto'])) < 9:
            messagebox.showerror("Error", "Número de celular inválido")
            return

        mensaje = (
            f"Estimado padre de familia, le recordamos que el alumno "
            f"{d['nombre']} presenta un saldo pendiente de S/. {d['deuda']:.2f} "
            f"en la Institución Educativa MUSUQ. Agradeceremos su pronto pago."
        )

        import urllib.parse
        mensaje_encoded = urllib.parse.quote(mensaje)
        url = f"https://web.whatsapp.com/send?phone=51{d['contacto']}&text={mensaje_encoded}"
        webbrowser.open(url)

    def imprimir_reporte(self):
        """Generar e imprimir reporte PDF"""
        if not HAS_REPORTLAB:
            messagebox.showerror(
                "Error",
                "ReportLab no está instalado.\nNo se puede generar PDF."
            )
            return

        if not self.data_total:
            messagebox.showwarning("Sin datos", "No hay información para imprimir")
            return

        # Preguntar dónde guardar
        fecha_str = datetime.now().strftime("%Y-%m-%d_%H%M")
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")],
            title="Guardar Reporte de Deudores",
            initialfile=f"Reporte_Deudores_{fecha_str}.pdf"
        )

        if not filename:
            return

        try:
            # Configurar PDF
            doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=1.5*cm)
            elements = []
            styles = getSampleStyleSheet()

            styles['Title'].fontSize = 18
            styles['Title'].alignment = 1

            # Encabezado
            titulo = Paragraph("Reporte de Morosidad - Sistema Musuq", styles['Title'])
            subtitulo = Paragraph(
                f"Fecha de emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                styles['Normal']
            )
            filtros = Paragraph(
                f"Filtros: Grupo={self.cb_grupo.get()} | Modalidad={self.cb_modalidad.get()}",
                styles['Normal']
            )

            elements.append(titulo)
            elements.append(Spacer(1, 10))
            elements.append(subtitulo)
            elements.append(filtros)
            elements.append(Spacer(1, 20))

            # Datos
            data = [['ALUMNO', 'MODALIDAD', 'CELULAR', 'DEUDA', 'ESTADO']]
            total_general = 0.0

            for d in self.data_total:
                row = [
                    d['nombre'],
                    d['modalidad'] or "",
                    d['contacto'],
                    f"S/. {d['deuda']:.2f}",
                    d['estado_desc']
                ]
                data.append(row)
                total_general += d['deuda']

            data.append(['', '', 'TOTAL GENERAL:', f"S/. {total_general:.2f}", ''])

            # Tabla
            t = Table(data, colWidths=[200, 80, 70, 70, 90])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))

            elements.append(t)
            doc.build(elements)

            messagebox.showinfo("Éxito", f"Reporte guardado correctamente en:\n{filename}")

            try:
                os.startfile(filename)
            except:
                pass

        except Exception as e:
            messagebox.showerror("Error", f"Error al crear el PDF:\n{str(e)}")
