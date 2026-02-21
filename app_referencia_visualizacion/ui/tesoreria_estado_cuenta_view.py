import customtkinter as ctk
from tkinter import messagebox
from app.controllers.tesoreria_controller import TesoreriaController

# --- IMPORTACIÓN DE ESTILOS ---
import app.styles.tabla_style as st

class EstadoCuentaView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.controller = TesoreriaController()
        self.alumno_seleccionado_id = None

        # Configuración Visual: Fondo General Oscuro
        self.configure(fg_color=st.Colors.BG_MAIN)

        # Layout: MISMAS POSICIONES
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=4) 
        self.grid_rowconfigure(0, weight=1)

        # ==========================================
        # PANEL IZQUIERDO: BÚSQUEDA (ESTILO DARK)
        # ==========================================
        # Aplicamos el color de fondo oscuro al panel izquierdo
        self.panel_izq = ctk.CTkFrame(self, width=220, corner_radius=10, fg_color=st.Colors.BG_PANEL)
        self.panel_izq.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew") # Sin padding externo para que llene el borde

        # Título
        ctk.CTkLabel(self.panel_izq, text="Estado de Cuenta", font=("Roboto", 16, "bold"), text_color="white").pack(pady=(20,5))
        ctk.CTkLabel(self.panel_izq, text="Alumno", font=("Roboto", 16, "bold"), text_color="white").pack()
        
        # Buscador Estilizado
        self.fr_search = ctk.CTkFrame(self.panel_izq, fg_color="#383838", height=35, corner_radius=10)
        self.fr_search.pack(fill="x", padx=10, pady=5)
        self.fr_search.pack_propagate(False)
        
        self.entry_busqueda = ctk.CTkEntry(self.fr_search, placeholder_text="🔍 Buscar...", 
                                           border_width=0, fg_color="transparent", text_color="white")
        self.entry_busqueda.pack(side="left", fill="both", expand=True, padx=5)
        self.entry_busqueda.bind("<KeyRelease>", self.buscar)

        # Lista de Resultados (Reemplazamos Treeview por ScrollableFrame para estilo Dark)
        self.scroll_lista = ctk.CTkScrollableFrame(self.panel_izq, fg_color="#383838")
        self.scroll_lista.pack(fill="both", expand=True, padx=5, pady=10)


        # ==========================================
        # PANEL DERECHO: DOCUMENTO (FORMATO ORIGINAL)
        # ==========================================
        # Mantenemos fg_color="white" como pediste
        self.panel_doc = ctk.CTkFrame(self, fg_color="white", corner_radius=0) 
        self.panel_doc.grid(row=0, column=1, padx=15, pady=10, sticky="nsew") # Padding 0 para unirlo

        # --- Cabecera del Documento ---
        fr_header = ctk.CTkFrame(self.panel_doc, fg_color="transparent")
        fr_header.pack(fill="x", padx=30, pady=20)

        ctk.CTkLabel(fr_header, text="ESTADO DE CUENTA", font=("Arial", 24, "bold"), text_color="#2c3e50").pack(side="left")
        
        # Botón Imprimir (Estilizado pero en su sitio)
        self.btn_print = ctk.CTkButton(fr_header, text="🖨️ Imprimir / PDF", 
                                       fg_color="#2c3e50", hover_color="#34495e", 
                                       height=35, font=("Arial", 11, "bold"),
                                       command=self.funcion_pendiente_pdf)
        self.btn_print.pack(side="right")

        ctk.CTkFrame(self.panel_doc, height=3, fg_color="#2c3e50").pack(fill="x", padx=30) # Línea divisoria más gruesa

        # --- Datos del Estudiante ---
        self.fr_info = ctk.CTkFrame(self.panel_doc, fg_color="#f8f9fa", corner_radius=5)
        self.fr_info.pack(fill="x", padx=30, pady=20)
        
        self.lbl_nombre = ctk.CTkLabel(self.fr_info, text="Seleccione un alumno...", font=("Arial", 18, "bold"), text_color="#2c3e50")
        self.lbl_nombre.pack(anchor="w", padx=20, pady=(10,0))
        
        self.lbl_detalles = ctk.CTkLabel(self.fr_info, text="--", font=("Arial", 12), text_color="#7f8c8d")
        self.lbl_detalles.pack(anchor="w", padx=20, pady=(0,10))

        # --- BARRA DE PROGRESO ---
        fr_progreso = ctk.CTkFrame(self.panel_doc, fg_color="transparent")
        fr_progreso.pack(fill="x", padx=30, pady=5)
        
        # Títulos alineados
        h_prog = ctk.CTkFrame(fr_progreso, fg_color="transparent")
        h_prog.pack(fill="x")
        ctk.CTkLabel(h_prog, text="Progreso de Pago:", font=("Arial", 11, "bold"), text_color="#555").pack(side="left")
        self.lbl_porcentaje = ctk.CTkLabel(h_prog, text="0% Pagado", font=("Arial", 12, "bold"), text_color="#27ae60")
        self.lbl_porcentaje.pack(side="right")
        
        self.progress_bar = ctk.CTkProgressBar(fr_progreso, height=12, corner_radius=6)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.configure(progress_color="#27ae60", fg_color="#e0e0e0")

        # --- TABLA DE RESUMEN (Manual para mejor estética en papel blanco) ---
        # Cabecera Tabla
        h_tab = ctk.CTkFrame(self.panel_doc, fg_color="#ecf0f1", height=30, corner_radius=0)
        h_tab.pack(fill="x", padx=30, pady=(10, 0))
        
        ctk.CTkLabel(h_tab, text="FECHA", width=100, font=("Arial", 10, "bold"), text_color="black").pack(side="left", padx=5)
        ctk.CTkLabel(h_tab, text="CONCEPTO", font=("Arial", 10, "bold"), text_color="black").pack(side="left", padx=5, expand=True)
        ctk.CTkLabel(h_tab, text="MONTO (S/.)", width=100, font=("Arial", 10, "bold"), text_color="black").pack(side="right", padx=15)

        # Cuerpo Tabla Scrollable (Misma posición que tu Treeview original)
        self.scroll_tabla_doc = ctk.CTkScrollableFrame(self.panel_doc, fg_color="transparent")
        self.scroll_tabla_doc.pack(fill="both", expand=True, padx=30, pady=(0, 10))

        # --- PIE DE PÁGINA ---
        fr_totales = ctk.CTkFrame(self.panel_doc, fg_color="#f4f6f7", height=60)
        fr_totales.pack(fill="x", padx=30, pady=20)

        self.lbl_total_deuda = ctk.CTkLabel(fr_totales, text="DEUDA TOTAL: S/. 0.00", font=("Arial", 16, "bold"), text_color="#c0392b")
        self.lbl_total_deuda.pack(side="right", padx=20, pady=15)

        ctk.CTkLabel(fr_totales, text="|", text_color="gray").pack(side="right")

        self.lbl_total_pagado = ctk.CTkLabel(fr_totales, text="PAGADO: S/. 0.00", font=("Arial", 16, "bold"), text_color="#27ae60")
        self.lbl_total_pagado.pack(side="right", padx=20, pady=15)

    # --- LÓGICA (Adaptada a la nueva lista visual) ---
    def buscar(self, event=None):
        criterio = self.entry_busqueda.get()
        
        # Limpiar lista visual izquierda
        for item in self.scroll_lista.winfo_children():
            item.destroy()
        
        resultados = self.controller.buscar_alumno(criterio)
        
        if not resultados:
            ctk.CTkLabel(self.scroll_lista, text="Sin resultados", text_color="gray").pack(pady=10)
            return

        for alu in resultados:
            # Botón estilo Dark Premium para la lista izquierda
            btn = ctk.CTkButton(self.scroll_lista, 
                                text=f"{alu.apell_paterno} {alu.nombres}\n{alu.dni}", 
                                fg_color="transparent", hover_color="#404040",
                                border_width=0, anchor="w", height=45,
                                text_color="silver", font=("Roboto", 12),
                                command=lambda id=alu.id: self.cargar_estado_cuenta(id))
            btn.pack(fill="x", pady=1)
            ctk.CTkFrame(self.scroll_lista, height=1, fg_color="#383838").pack(fill="x") # Separador

    def cargar_estado_cuenta(self, id_alumno):
        datos = self.controller.obtener_estado_cuenta(id_alumno)
        if not datos: return

        # 1. Info Header
        self.lbl_nombre.configure(text=datos['nombre_completo'])
        self.lbl_detalles.configure(text=f"DNI: {datos['dni']}   |   Código: {datos['codigo']}   |   {datos['info_extra']}")

        # 2. Barra de Progreso
        costo = datos['costo']
        pagado = datos['pagado']
        
        if costo > 0:
            porcentaje = pagado / costo
            if porcentaje > 1: porcentaje = 1 
        else:
            porcentaje = 1.0 if pagado > 0 else 0.0

        self.progress_bar.set(porcentaje)
        self.lbl_porcentaje.configure(text=f"{porcentaje*100:.0f}% Pagado")

        # 3. Tabla (Filas manuales estilo documento)
        for w in self.scroll_tabla_doc.winfo_children(): w.destroy()
        
        if not datos['historial']:
            ctk.CTkLabel(self.scroll_tabla_doc, text="Sin movimientos.", text_color="gray").pack(pady=20)
        else:
            for i, pago in enumerate(datos['historial']):
                # Alternar colores filas (blanco/gris muy claro) para legibilidad
                bg_row = "white" if i % 2 == 0 else "#fcfcfc"
                
                row = ctk.CTkFrame(self.scroll_tabla_doc, fg_color=bg_row, corner_radius=0, height=30)
                row.pack(fill="x", pady=0)
                
                ctk.CTkLabel(row, text=pago.fecha, width=100, text_color="#333", font=("Arial", 10)).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=pago.concepto, text_color="#333", font=("Arial", 10), anchor="w").pack(side="left", padx=5, expand=True, fill="x")
                ctk.CTkLabel(row, text=f"S/. {pago.monto:.2f}", width=100, text_color="black", font=("Arial", 10, "bold")).pack(side="right", padx=15)
                
                # Línea fina separadora
                ctk.CTkFrame(self.scroll_tabla_doc, height=1, fg_color="#eee").pack(fill="x")

        # 4. Totales
        self.lbl_total_pagado.configure(text=f"PAGADO: S/. {pagado:.2f}")
        self.lbl_total_deuda.configure(text=f"DEUDA TOTAL: S/. {datos['deuda']:.2f}")

    def funcion_pendiente_pdf(self):
        messagebox.showinfo("Próximamente", "Aquí se abrirá el PDF para imprimir.")