import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
import webbrowser
import os
import math
from datetime import datetime

# --- IMPORTACIONES PARA PDF (REPORTLAB) ---
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

# Controladores y Estilos
from app.controllers.rep_deudores_controller import RepDeudoresController
import app.styles.tabla_style as st

class RepDeudoresView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.controller = RepDeudoresController()
        
        # --- CONFIGURACIÓN HÍBRIDA (CEREBRO) ---
        self.data_total = []            # Base de datos completa en RAM
        self.data_pagina = []           # Los 100 de esta página
        
        # 1. Paginación (Macro)
        self.pag_actual = 1
        self.items_por_pag = 100        # 100 por página
        self.total_pags = 1
        
        # 2. Scroll Infinito (Micro)
        self.items_visibles = 0         
        self.lote_scroll = 25           # Carga de 25 en 25
        self.lock_carga = False
        
        self.seleccionado = None        # Dato seleccionado
        self.seleccionado_widget = None # Widget visual seleccionado

        # Configuración Visual
        self.configure(fg_color=st.Colors.BG_MAIN)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Anchos visuales
        self.W_COL = [40, 250, 100, 100, 80, 80, 80, 120]

        # ==================== 1. FILTROS ====================
        fr_top = ctk.CTkFrame(self, height=80, fg_color=st.Colors.BG_PANEL, corner_radius=10)
        fr_top.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        ctk.CTkLabel(fr_top, text="REPORTE DE MOROSIDAD", font=("Roboto", 18, "bold"), text_color="white").pack(side="left", padx=20)

        grupos, modalidades = self.controller.obtener_filtros_disponibles()

        ctk.CTkLabel(fr_top, text="Grupo:", text_color="silver").pack(side="left", padx=5)
        self.cb_grupo = ctk.CTkComboBox(fr_top, values=["Todos"] + grupos, width=100, 
                                        command=self.cargar_datos, 
                                        fg_color="#383838", text_color="white", dropdown_fg_color="#2b2b2b")
        self.cb_grupo.pack(side="left", padx=5)

        ctk.CTkLabel(fr_top, text="Modalidad:", text_color="silver").pack(side="left", padx=5)
        self.cb_modalidad = ctk.CTkComboBox(fr_top, values=["Todas"] + modalidades, width=140, 
                                            command=self.cargar_datos,
                                            fg_color="#383838", text_color="white", dropdown_fg_color="#2b2b2b")
        self.cb_modalidad.pack(side="left", padx=5)

        # KPI Deuda
        self.fr_kpi = ctk.CTkFrame(fr_top, fg_color="#922b21", corner_radius=6, border_width=1, border_color="#c0392b")
        self.fr_kpi.pack(side="right", padx=20, pady=10)
        self.lbl_total_deuda = ctk.CTkLabel(self.fr_kpi, text="S/. 0.00", font=("Arial", 20, "bold"), text_color="white")
        self.lbl_total_deuda.pack(padx=15, pady=(5,0))
        ctk.CTkLabel(self.fr_kpi, text="DEUDA TOTAL", font=("Arial", 9), text_color="#ecf0f1").pack(padx=15, pady=(0,5))

        # ==================== 2. TABLA ====================
        self.fr_tabla_bg = ctk.CTkFrame(self, fg_color=st.Colors.BG_PANEL, corner_radius=10)
        self.fr_tabla_bg.grid(row=1, column=0, sticky="nsew", padx=20, pady=5)

        # Cabecera
        h_frame = ctk.CTkFrame(self.fr_tabla_bg, height=40, fg_color=st.Colors.TABLE_HEADER, corner_radius=5)
        h_frame.pack(fill="x", padx=5, pady=(5,0))
        cols = ["#", "ALUMNO", "MODALIDAD", "CONTACTO", "COSTO", "PAGADO", "DEUDA", "ESTADO"]
        for i, c in enumerate(cols):
            w = self.W_COL[i]
            anchor = "w" if i == 1 else "center"
            ctk.CTkLabel(h_frame, text=c, width=w, anchor=anchor, font=("Roboto", 11, "bold"), text_color="white").pack(side="left", padx=2)

        self.lbl_loading = ctk.CTkLabel(self.fr_tabla_bg, text="Cargando...", text_color="#f39c12")
        
        self.scroll_tabla = ctk.CTkScrollableFrame(self.fr_tabla_bg, fg_color="transparent")
        self.scroll_tabla.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Hook Scroll Infinito
        self.scroll_tabla._parent_canvas.configure(yscrollcommand=self._evento_scroll)

        # ==================== 3. PAGINACIÓN Y ACCIONES ====================
        fr_bottom = ctk.CTkFrame(self, fg_color="transparent", height=50)
        fr_bottom.grid(row=2, column=0, sticky="ew", padx=20, pady=20)

        ctk.CTkButton(fr_bottom, text="🔄 Actualizar", command=self.cargar_datos, fg_color="gray", width=100).pack(side="left")

        # Paginación
        fr_pag = ctk.CTkFrame(fr_bottom, fg_color="transparent")
        fr_pag.pack(side="left", expand=True)
        self.btn_ant = ctk.CTkButton(fr_pag, text="< Ant", width=60, fg_color="#2b2b2b", command=lambda: self.cambiar_pag(-1))
        self.btn_ant.pack(side="left", padx=10)
        self.lbl_pag = ctk.CTkLabel(fr_pag, text="Pag 1/1", font=("Roboto", 12, "bold"), text_color="white")
        self.lbl_pag.pack(side="left", padx=10)
        self.btn_sig = ctk.CTkButton(fr_pag, text="Sig >", width=60, fg_color="#2b2b2b", command=lambda: self.cambiar_pag(1))
        self.btn_sig.pack(side="left", padx=10)

        # Botones Derechos
        ctk.CTkButton(fr_bottom, text="📱 WhatsApp", fg_color="#25D366", hover_color="#128C7E", command=self.enviar_whatsapp).pack(side="right", padx=5)
        ctk.CTkButton(fr_bottom, text="🖨️ Imprimir", fg_color="#2980b9", command=self.imprimir_reporte).pack(side="right", padx=5)

        self.cargar_datos()

    # ==================== LÓGICA DE HILOS Y DATOS ====================
    def cargar_datos(self, event=None):
        self.lbl_loading.pack(pady=5)
        self.btn_ant.configure(state="disabled")
        self.btn_sig.configure(state="disabled")
        for w in self.scroll_tabla.winfo_children(): w.destroy()
        
        g, m = self.cb_grupo.get(), self.cb_modalidad.get()
        threading.Thread(target=self._proceso_en_segundo_plano, args=(g, m), daemon=True).start()

    def _proceso_en_segundo_plano(self, grupo, modalidad):
        datos = self.controller.obtener_lista_deudores(grupo, modalidad)
        total = sum(d["deuda"] for d in datos)
        self.after(0, lambda: self._finalizar_carga(datos, total))

    def _finalizar_carga(self, datos, total):
        self.lbl_loading.pack_forget()
        self.lbl_total_deuda.configure(text=f"S/. {total:,.2f}")
        
        self.data_total = datos
        
        if not datos:
            self.total_pags = 1
            ctk.CTkLabel(self.scroll_tabla, text="No hay datos.", text_color="gray").pack(pady=20)
        else:
            self.total_pags = math.ceil(len(datos) / self.items_por_pag)
            
        self.pag_actual = 1
        self.renderizar_pagina()

    # ==================== PAGINACIÓN + SCROLL INFINITO ====================
    def cambiar_pag(self, direccion):
        nuevo = self.pag_actual + direccion
        if 1 <= nuevo <= self.total_pags:
            self.pag_actual = nuevo
            self.renderizar_pagina()

    def renderizar_pagina(self):
        for w in self.scroll_tabla.winfo_children(): w.destroy()
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
        self.scroll_tabla._scrollbar.set(first, last)
        if self.lock_carga: return
        try:
            if float(last) > 0.90 and self.items_visibles < len(self.data_pagina):
                self.lock_carga = True
                self.after(10, self._pintar_lote_scroll)
        except: pass

    def _pintar_lote_scroll(self):
        inicio = self.items_visibles
        fin = inicio + self.lote_scroll
        sub_lote = self.data_pagina[inicio:fin]
        
        for i, d in enumerate(sub_lote):
            idx = (self.pag_actual - 1) * self.items_por_pag + inicio + i + 1
            self.crear_fila_visual(d, idx)
            
        self.items_visibles += len(sub_lote)
        self.lock_carga = False

    def crear_fila_visual(self, d, index):
        bg = st.Colors.ROW_ODD if index % 2 == 0 else st.Colors.ROW_EVEN
        row = ctk.CTkFrame(self.scroll_tabla, fg_color=bg, corner_radius=5, height=35)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        
        row.bind("<Button-1>", lambda e: self.seleccionar_fila(row, d))

        def add_cell(txt, w, color="white", anchor="center"):
            lbl = ctk.CTkLabel(row, text=str(txt), width=w, anchor=anchor, text_color=color, font=("Roboto", 11))
            lbl.pack(side="left", padx=2)
            lbl.bind("<Button-1>", lambda e: self.seleccionar_fila(row, d))

        add_cell(d['icono'], self.W_COL[0])
        add_cell(d['nombre'], self.W_COL[1], anchor="w")
        add_cell(d['modalidad'], self.W_COL[2], "gray")
        add_cell(d['contacto'], self.W_COL[3], "silver")
        add_cell(f"S/. {d['costo']:.2f}", self.W_COL[4], "gray", "e")
        add_cell(f"S/. {d['pagado']:.2f}", self.W_COL[5], "#2ecc71", "e")
        add_cell(f"S/. {d['deuda']:.2f}", self.W_COL[6], "#e74c3c", "e")
        
        col_badge = "#c0392b" if d['tag'] == "CRITICO" else ("#e67e22" if d['tag'] == "MEDIO" else "#2ecc71")
        f_badge = ctk.CTkFrame(row, fg_color=col_badge, width=self.W_COL[7], height=25, corner_radius=10)
        f_badge.pack(side="left", padx=2)
        l_badge = ctk.CTkLabel(f_badge, text=d['estado_desc'], text_color="white", font=("Arial", 10, "bold"))
        l_badge.place(relx=0.5, rely=0.5, anchor="center")
        
        f_badge.bind("<Button-1>", lambda e: self.seleccionar_fila(row, d))
        l_badge.bind("<Button-1>", lambda e: self.seleccionar_fila(row, d))

    def seleccionar_fila(self, widget, data):
        if self.seleccionado_widget and self.seleccionado_widget.winfo_exists():
            try: self.seleccionado_widget.configure(fg_color=self.bg_anterior)
            except: pass
            
        self.seleccionado_widget = widget
        self.bg_anterior = widget.cget("fg_color")
        self.seleccionado = data
        widget.configure(fg_color="#34495e")

    # ==================== ACCIONES ====================
    def enviar_whatsapp(self):
        if not self.seleccionado:
            messagebox.showwarning("Aviso", "Seleccione un alumno de la lista.")
            return
        d = self.seleccionado
        if len(str(d['contacto'])) < 9:
            messagebox.showerror("Error", "Número celular inválido.")
            return
        mensaje = f"Estimado padre de familia, le recordamos que el alumno {d['nombre']} presenta un saldo pendiente de S/. {d['deuda']:.2f} en la Institución Educativa MUSUQ. Agradeceremos su pronto pago."
        import urllib.parse
        mensaje_encoded = urllib.parse.quote(mensaje)
        url = f"https://web.whatsapp.com/send?phone=51{d['contacto']}&text={mensaje_encoded}"
        webbrowser.open(url)

    def imprimir_reporte(self):
        # Usamos self.data_total para imprimir TODO lo filtrado, no solo lo visible
        if not self.data_total:
            messagebox.showwarning("Sin datos", "No hay información en la tabla para imprimir.")
            return

        # 1. Preguntar dónde guardar el archivo
        fecha_str = datetime.now().strftime("%Y-%m-%d_%H%M")
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")],
            title="Guardar Reporte de Deudores",
            initialfile=f"Reporte_Deudores_{fecha_str}.pdf"
        )

        if not filename:
            return  # El usuario canceló

        try:
            # 2. Configuración del PDF
            doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=60 - 1.5*cm)
            elements = []
            styles = getSampleStyleSheet()

            # Estilo personalizado para el título
            styles['Title'].fontSize = 18
            styles['Title'].alignment = 1 # Center

            # 3. Encabezado del reporte
            titulo = Paragraph(f"Reporte de Morosidad - Sistema Musuq", styles['Title'])
            subtitulo = Paragraph(f"Fecha de emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal'])
            filtros = Paragraph(f"<b>Filtros aplicados:</b> Grupo={self.cb_grupo.get()} | Modalidad={self.cb_modalidad.get()}", styles['Normal'])
            
            elements.append(titulo)
            elements.append(Spacer(1, 10))
            elements.append(subtitulo)
            elements.append(filtros)
            elements.append(Spacer(1, 20))

            # 4. Preparar datos de la tabla
            # Encabezados de la tabla PDF (TU FORMATO ORIGINAL)
            data = [['ALUMNO', 'MODALIDAD', 'CELULAR', 'DEUDA', 'ESTADO']]
            
            total_general = 0.0

            # Llenar filas (Usando self.data_total para incluir todos los registros filtrados)
            for d in self.data_total:
                row = [
                    d['nombre'],          # Alumno
                    d['modalidad'] or "", # Mod
                    d['contacto'],        # Celular
                    f"S/. {d['deuda']:.2f}", # Deuda
                    d['estado_desc']      # Estado
                ]
                data.append(row)
                total_general += d['deuda']

            # Fila final de totales
            data.append(['', '', 'TOTAL GENERAL:', f"S/. {total_general:.2f}", ''])

            # 5. Crear la Tabla ReportLab (TUS ANCHOS ORIGINALES)
            t = Table(data, colWidths=[200, 80, 70, 70, 90])

            # Estilos visuales de la tabla (TUS COLORES ORIGINALES)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),    # Fondo encabezado
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),   # Texto encabezado
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),               # Alineación general
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),                  # Alinear nombres a la izq
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),     # Fuente encabezado
                ('FONTSIZE', (0, 0), (-1, -1), 9),                   # Tamaño letra
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),              # Espacio headers
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),        # Bordes
                
                # Fila de totales (última fila)
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))

            elements.append(t)

            # 6. Generar el PDF
            doc.build(elements)

            messagebox.showinfo("Éxito", f"Reporte guardado correctamente en:\n{filename}")
            
            # Opcional: Abrir el archivo automáticamente
            try:
                os.startfile(filename)
            except:
                pass

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al crear el PDF:\n{str(e)}")