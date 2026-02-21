import customtkinter as ctk
from tkinter import ttk, messagebox
from app.controllers.tesoreria_controller import TesoreriaController

# --- IMPORTACIÓN DE ESTILOS ---
import app.styles.tabla_style as st

class TesoreriaView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.controller = TesoreriaController()
        self.alumno_seleccionado_id = None
        self.deuda_actual_cache = 0.0

        # Configuración Visual General
        self.configure(fg_color=st.Colors.BG_MAIN)

        # --- Layout Principal ---
        self.grid_columnconfigure(0, weight=1) # Búsqueda (Izquierda)
        self.grid_columnconfigure(1, weight=3) # Detalles (Derecha)
        self.grid_rowconfigure(0, weight=1)

        # ============================================================
        #              PANEL IZQUIERDO: BÚSQUEDA
        # ============================================================
        panel_izq = ctk.CTkFrame(self, width=280, fg_color=st.Colors.BG_MAIN, corner_radius=0)
        panel_izq.grid(row=0, column=0, padx=(0, 2), pady=0, sticky="nsew")
        panel_izq.pack_propagate(False)

        # Título
        ctk.CTkLabel(panel_izq, text="TESORERÍA", font=st.Fonts.TITLE, text_color="white").pack(pady=(30, 10))
        ctk.CTkLabel(panel_izq, text="Gestión de Pagos y Deudas", font=("Roboto", 12), text_color="gray").pack(pady=(0, 20))

        # Buscador
        fr_search = ctk.CTkFrame(panel_izq, fg_color="transparent")
        fr_search.pack(fill="x", padx=15, pady=5)
        
        self.bg_search = ctk.CTkFrame(fr_search, fg_color="#383838", corner_radius=20, height=40)
        self.bg_search.pack(fill="x")
        self.bg_search.pack_propagate(False)
        
        ctk.CTkLabel(self.bg_search, text="🔍", font=("Arial", 14), text_color="gray").pack(side="left", padx=(15, 5))
        self.entry_busqueda = ctk.CTkEntry(self.bg_search, placeholder_text="Buscar DNI o Nombre...", 
                                         border_width=0, fg_color="transparent", text_color="white")
        self.entry_busqueda.pack(side="left", fill="both", expand=True)
        self.entry_busqueda.bind("<KeyRelease>", self.buscar) 

        # Lista de Resultados (Custom Scrollable en lugar de Treeview feo)
        ctk.CTkLabel(panel_izq, text="Resultados:", font=("Roboto", 11, "bold"), text_color="gray").pack(anchor="w", padx=20, pady=(15, 5))
        
        self.scroll_resultados = ctk.CTkScrollableFrame(panel_izq, fg_color="#2b2b2b")
        self.scroll_resultados.pack(fill="both", expand=True, padx=15, pady=10)

        # ============================================================
        #              PANEL DERECHO: DETALLES
        # ============================================================
        panel_der = ctk.CTkFrame(self, fg_color="transparent") # Fondo transparente para ver el BG_MAIN
        panel_der.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

        # ------------------------------------------------------------
        # 1. RECUADRO NARANJA (DATOS DEL ALUMNO) - Estilo Card
        # ------------------------------------------------------------
        self.fr_datos_alumno = ctk.CTkFrame(panel_der, fg_color=st.Colors.BG_PANEL, 
                                            border_color="#e67e22", border_width=2, corner_radius=10)
        self.fr_datos_alumno.pack(fill="x", pady=(0, 15))

        # Título del recuadro
        ctk.CTkLabel(self.fr_datos_alumno, text="INFORMACIÓN DEL ESTUDIANTE", 
                     text_color="#e67e22", font=("Roboto", 11, "bold")).pack(pady=(10,5))

        # Grid interno
        self.fr_datos_grid = ctk.CTkFrame(self.fr_datos_alumno, fg_color="transparent")
        self.fr_datos_grid.pack(fill="x", padx=20, pady=(0, 15))

        # Variables de Texto
        self.var_nombre = ctk.StringVar(value="Seleccione un alumno...")
        self.var_dni = ctk.StringVar(value="--")
        self.var_codigo = ctk.StringVar(value="--")

        # Etiquetas Estilizadas
        # Fila 1: Icono + Nombre Grande
        ctk.CTkLabel(self.fr_datos_grid, text="👤", font=("Arial", 24)).grid(row=0, column=0, rowspan=2, padx=(0, 10))
        self.lbl_nombre = ctk.CTkLabel(self.fr_datos_grid, textvariable=self.var_nombre, font=("Roboto", 18, "bold"), text_color="white", anchor="w")
        self.lbl_nombre.grid(row=0, column=1, columnspan=3, sticky="w")

        # Fila 2: Datos técnicos
        f_subdatos = ctk.CTkFrame(self.fr_datos_grid, fg_color="transparent")
        f_subdatos.grid(row=1, column=1, columnspan=3, sticky="w")
        
        ctk.CTkLabel(f_subdatos, text="DNI: ", text_color="gray", font=("Roboto", 12)).pack(side="left")
        ctk.CTkLabel(f_subdatos, textvariable=self.var_dni, text_color="silver", font=("Roboto", 12, "bold")).pack(side="left")
        ctk.CTkLabel(f_subdatos, text="   |   CÓDIGO: ", text_color="gray", font=("Roboto", 12)).pack(side="left")
        ctk.CTkLabel(f_subdatos, textvariable=self.var_codigo, text_color="#f1c40f", font=("Roboto", 12, "bold")).pack(side="left")

        # ------------------------------------------------------------
        # 2. TARJETAS FINANCIERAS (KPIs)
        # ------------------------------------------------------------
        fr_resumen = ctk.CTkFrame(panel_der, fg_color="transparent")
        fr_resumen.pack(fill="x", pady=10)
        
        # Guardamos referencias a los labels de valor para actualizar
        self.lbl_val_costo = self.crear_tarjeta(fr_resumen, "COSTO TOTAL", "S/. 0.00", "#7f8c8d", "💰")
        self.lbl_val_pagado = self.crear_tarjeta(fr_resumen, "TOTAL PAGADO", "S/. 0.00", "#27ae60", "✅")
        self.lbl_val_deuda = self.crear_tarjeta(fr_resumen, "DEUDA PENDIENTE", "S/. 0.00", "#c0392b", "🚨")

        self.card_costo = self.lbl_val_costo # Mantener compatibilidad de nombres
        self.card_pagado = self.lbl_val_pagado
        self.card_deuda = self.lbl_val_deuda

        # ------------------------------------------------------------
        # 3. CAJA (INPUTS)
        # ------------------------------------------------------------
        self.fr_caja = ctk.CTkFrame(panel_der, fg_color=st.Colors.BG_PANEL, corner_radius=10)
        self.fr_caja.pack(fill="x", pady=0)
        
        # Header Caja
        h_caja = ctk.CTkFrame(self.fr_caja, fg_color="#2c3e50", height=30, corner_radius=10)
        h_caja.pack(fill="x", padx=2, pady=2)
        ctk.CTkLabel(h_caja, text="  💳  REGISTRAR NUEVO ABONO", font=("Roboto", 12, "bold"), text_color="white").pack(side="left")

        fr_inputs = ctk.CTkFrame(self.fr_caja, fg_color="transparent")
        fr_inputs.pack(pady=15, padx=15, fill="x")
        
        # Inputs
        self.entry_monto = ctk.CTkEntry(fr_inputs, placeholder_text="Monto S/.", width=100, font=("Roboto", 14), justify="center")
        self.entry_monto.pack(side="left", padx=(0, 10))
        
        self.entry_concepto = ctk.CTkEntry(fr_inputs, placeholder_text="Concepto (Ejm: Pensión Marzo)", width=250)
        self.entry_concepto.pack(side="left", padx=5, fill="x", expand=True)
        
        self.btn_pagar = ctk.CTkButton(fr_inputs, text="COBRAR", fg_color="#27ae60", hover_color="#2ecc71", 
                                     command=self.realizar_pago, state="disabled", width=120, font=("Roboto", 12, "bold"))
        self.btn_pagar.pack(side="left", padx=10)
        
        self.btn_cobrar_todo = ctk.CTkButton(fr_inputs, text="TODO", fg_color="#2980b9", hover_color="#3498db",
                                           width=80, command=self.cobrar_todo, state="disabled")
        self.btn_cobrar_todo.pack(side="left")

        # ------------------------------------------------------------
        # 4. HISTORIAL (Tabla Custom)
        # ------------------------------------------------------------
        ctk.CTkLabel(panel_der, text="HISTORIAL DE MOVIMIENTOS", font=("Roboto", 14, "bold"), text_color="silver").pack(anchor="w", pady=(5, 5))
        
        # Contenedor Tabla
        self.fr_tabla_historial = ctk.CTkFrame(panel_der, fg_color=st.Colors.BG_PANEL, corner_radius=10)
        self.fr_tabla_historial.pack(fill="both", expand=True)

        # Cabecera Manual
        h_hist = ctk.CTkFrame(self.fr_tabla_historial, height=35, fg_color="#383838", corner_radius=5)
        h_hist.pack(fill="x", padx=5, pady=(5,0))
        ctk.CTkLabel(h_hist, text="FECHA", width=100, text_color="white", font=("Arial", 11, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(h_hist, text="CONCEPTO", width=300, text_color="white", font=("Arial", 11, "bold"), anchor="w").pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkLabel(h_hist, text="MONTO", width=100, text_color="white", font=("Arial", 11, "bold")).pack(side="right", padx=15)

        # Cuerpo Scrollable
        self.scroll_historial = ctk.CTkScrollableFrame(self.fr_tabla_historial, fg_color="transparent")
        self.scroll_historial.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Mensaje vacío
        self.lbl_vacio = ctk.CTkLabel(self.scroll_historial, text="Sin movimientos", text_color="gray")
        self.lbl_vacio.pack(pady=20)

        # Iniciar
        self.buscar() 

    def crear_tarjeta(self, parent, titulo, valor, color, icono):
        card = ctk.CTkFrame(parent, fg_color=st.Colors.BG_PANEL, corner_radius=10, height=80)
        card.pack(side="left", padx=5, expand=True, fill="x")
        card.pack_propagate(False) 
        
        # Barra lateral de color
        bar = ctk.CTkFrame(card, width=5, fg_color=color, corner_radius=0)
        bar.pack(side="left", fill="y", padx=(0, 10))
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, pady=5)
        
        ctk.CTkLabel(content, text=titulo, text_color="gray", font=("Roboto", 10, "bold")).pack(anchor="w")
        
        lbl_val = ctk.CTkLabel(content, text=valor, text_color="white", font=("Roboto", 20, "bold"))
        lbl_val.pack(anchor="w", pady=(0, 0))
        
        # Icono flotante
        ctk.CTkLabel(card, text=icono, font=("Arial", 25), text_color="#5A5A5A").pack(side="right", padx=10)
        
        return lbl_val

    # ============================================================
    #                  LÓGICA DEL NEGOCIO
    # ============================================================

    def buscar(self, event=None):
        criterio = self.entry_busqueda.get()
        
        # Limpiar lista visual
        for widget in self.scroll_resultados.winfo_children():
            widget.destroy()
            
        resultados = self.controller.buscar_alumno(criterio)
        
        if not resultados:
            ctk.CTkLabel(self.scroll_resultados, text="Sin resultados", text_color="gray").pack(pady=10)
            return

        for alu in resultados:
            # Tarjeta de resultado
            btn = ctk.CTkButton(self.scroll_resultados, 
                                text=f"{alu.apell_paterno} {alu.nombres}\nTargeta: {alu.dni}", 
                                fg_color="transparent", 
                                hover_color="#404040",
                                border_width=0, 
                                anchor="w",
                                height=45,
                                text_color="silver",
                                font=("Roboto", 12),
                                command=lambda id=alu.id: self.seleccionar_alumno(id))
            btn.pack(fill="x", pady=1)
            # Separador
            ctk.CTkFrame(self.scroll_resultados, height=1, fg_color="#383838").pack(fill="x")

    def seleccionar_alumno(self, id_alumno):
        self.alumno_seleccionado_id = id_alumno
        self.btn_pagar.configure(state="normal")
        self.btn_cobrar_todo.configure(state="normal")
        self.actualizar_estado_cuenta()

    def actualizar_estado_cuenta(self):
        """Llenar la UI con datos"""
        datos = self.controller.obtener_estado_cuenta(self.alumno_seleccionado_id)
        if not datos: return

        self.deuda_actual_cache = datos["deuda"]

        # 1. Datos Alumno
        self.var_nombre.set(datos["nombre_completo"])
        self.var_dni.set(datos["dni"])
        self.var_codigo.set(datos["codigo"])

        # 2. Tarjetas
        self.card_costo.configure(text=f"S/. {datos['costo']:.2f}")
        self.card_pagado.configure(text=f"S/. {datos['pagado']:.2f}")
        self.card_deuda.configure(text=f"S/. {datos['deuda']:.2f}")

        # 3. Historial (Tabla Custom)
        for w in self.scroll_historial.winfo_children(): w.destroy()
        
        if not datos["historial"]:
            ctk.CTkLabel(self.scroll_historial, text="No hay pagos registrados", text_color="gray").pack(pady=20)
        else:
            for i, pago in enumerate(datos["historial"]):
                bg = st.Colors.ROW_ODD if i % 2 == 0 else st.Colors.ROW_EVEN
                row = ctk.CTkFrame(self.scroll_historial, fg_color=bg, corner_radius=5, height=35)
                row.pack(fill="x", pady=2)
                row.pack_propagate(False)
                
                # Celdas
                ctk.CTkLabel(row, text=pago.fecha, width=100, text_color="white", font=("Roboto Mono", 11)).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=pago.concepto, text_color="gray", anchor="w").pack(side="left", padx=5, fill="x", expand=True)
                ctk.CTkLabel(row, text=f"S/. {pago.monto:.2f}", width=100, text_color="#2ecc71", font=("Roboto", 11, "bold")).pack(side="right", padx=15)

    def cobrar_todo(self):
        if self.deuda_actual_cache <= 0:
            messagebox.showinfo("Información", "El alumno no tiene deuda pendiente.")
            return
        self.entry_monto.delete(0, "end")
        self.entry_monto.insert(0, f"{self.deuda_actual_cache:.2f}")
        self.entry_concepto.delete(0, "end")
        self.entry_concepto.insert(0, "Cancelación Total")

    def realizar_pago(self):
        try:
            monto_str = self.entry_monto.get()
            if not monto_str: return
            monto = float(monto_str)
            concepto = self.entry_concepto.get()
            
            if monto <= 0:
                messagebox.showwarning("Error", "Monto inválido.")
                return
            
            if not messagebox.askyesno("Confirmar", f"¿Registrar pago de S/. {monto:.2f}?"):
                return
            
            exito, msg = self.controller.registrar_pago(self.alumno_seleccionado_id, monto, concepto)
            
            if exito:
                messagebox.showinfo("Éxito", msg)
                self.entry_monto.delete(0, "end")
                self.entry_concepto.delete(0, "end")
                self.actualizar_estado_cuenta()
            else:
                messagebox.showerror("Error", msg)
        except ValueError:
            messagebox.showerror("Error", "Monto inválido")