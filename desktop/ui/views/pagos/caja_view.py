"""
Vista de Caja/Tesorería - ESTILO PREMIUM MEJORADO
Sistema Musuq Cloud
Gestión de pagos, cobros y estado de cuenta de alumnos
"""

import customtkinter as ctk
from tkinter import messagebox
from customtkinter import CTkFont

from controllers.pagos_controller import PagosController
from styles import tabla_style as st
from core.theme_manager import ThemeManager as TM


class CajaView(ctk.CTkFrame):
    """
    Vista profesional para gestión de tesorería.
    Características: Búsqueda, KPIs financieros, registro de pagos, historial
    """

    def __init__(self, parent, auth_client=None):
        super().__init__(parent, fg_color="transparent")

        if not auth_client:
            raise ValueError("auth_client es requerido para inicializar CajaView")

        self.auth_client = auth_client
        self.controller = PagosController(auth_client.token)
        self.alumno_seleccionado_id = None
        self.deuda_actual_cache = 0.0
        self._debounce_timer = None  # Timer para debounce

        self.crear_ui()
        self.buscar()

    # ... (skipping to buscar method) ...



    def crear_ui(self):
        """Crear interfaz completa"""
        # Layout principal: Grid 2 columnas
        self.grid_columnconfigure(0, weight=1, minsize=320)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # Panel izquierdo: Búsqueda
        self._crear_panel_busqueda()

        # Panel derecho: Detalles
        self._crear_panel_detalles()

    # ========================================================
    # PANEL IZQUIERDO: BÚSQUEDA
    # ========================================================

    def _crear_panel_busqueda(self):
        """Crear panel izquierdo con búsqueda de alumnos"""
        panel_izq = ctk.CTkFrame(
            self,
            width=320,
            fg_color=TM.bg_panel(),
            corner_radius=10
        )
        panel_izq.grid(row=0, column=0, padx=(15, 2), pady=15, sticky="nsew")
        panel_izq.pack_propagate(False)

        # Header con icono
        self._crear_header_busqueda(panel_izq)

        # Separador
        ctk.CTkFrame(
            panel_izq,
            height=2,
            fg_color="#404040"
        ).pack(fill="x", padx=20, pady=15)

        # Buscador
        self._crear_buscador(panel_izq)

        # Label "Resultados"
        ctk.CTkLabel(
            panel_izq,
            text="Resultados:",
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text_secondary(),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(15, 8))

        # Lista de resultados
        self.scroll_resultados = ctk.CTkScrollableFrame(
            panel_izq,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.scroll_resultados.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def _crear_header_busqueda(self, parent):
        """Crear header del panel de búsqueda"""
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(25, 0))

        # Icono grande
        ctk.CTkLabel(
            header,
            text="💰",
            font=CTkFont(family="Arial", size=50)
        ).pack(pady=(0, 10))

        # Título
        ctk.CTkLabel(
            header,
            text="TESORERÍA",
            font=CTkFont(family="Roboto", size=20, weight="bold"),
            text_color=TM.text()
        ).pack()

        # Subtítulo
        ctk.CTkLabel(
            header,
            text="Gestión de Pagos y Deudas",
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(pady=(2, 0))

    def _crear_buscador(self, parent):
        """Crear frame de búsqueda"""
        fr_search = ctk.CTkFrame(parent, fg_color="transparent")
        fr_search.pack(fill="x", padx=15, pady=0)

        # Frame búsqueda
        self.bg_search = ctk.CTkFrame(
            fr_search,
            fg_color=TM.bg_card(),
            corner_radius=10,
            height=45
        )
        self.bg_search.pack(fill="x")
        self.bg_search.pack_propagate(False)

        # Icono búsqueda
        ctk.CTkLabel(
            self.bg_search,
            text="🔍",
            font=CTkFont(family="Arial", size=16),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(15, 8))

        # Entry
        self.entry_busqueda = ctk.CTkEntry(
            self.bg_search,
            placeholder_text="Buscar DNI o Nombre...",
            border_width=0,
            fg_color="transparent",
            text_color=TM.text(),
            font=CTkFont(family="Roboto", size=12)
        )
        self.entry_busqueda.pack(side="left", fill="both", expand=True, padx=(0, 15))
        self.entry_busqueda.bind("<KeyRelease>", self.buscar)

    # ========================================================
    # PANEL DERECHO: DETALLES
    # ========================================================

    def _crear_panel_detalles(self):
        """Crear panel derecho con detalles del alumno"""
        panel_der = ctk.CTkFrame(self, fg_color="transparent")
        panel_der.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

        # 1. Datos del alumno
        self._crear_card_datos_alumno(panel_der)

        # 2. Tarjetas KPI
        self._crear_tarjetas_kpi(panel_der)

        # 3. Caja de pagos
        self._crear_caja_pagos(panel_der)

        # 4. Historial
        self._crear_historial(panel_der)

    def _crear_card_datos_alumno(self, parent):
        """Crear card con datos del alumno"""
        self.fr_datos_alumno = ctk.CTkFrame(
            parent,
            fg_color=TM.bg_card(),
            border_color=TM.warning(),
            border_width=2,
            corner_radius=10
        )
        self.fr_datos_alumno.pack(fill="x", pady=(0, 15))

        # Container interno
        container = ctk.CTkFrame(self.fr_datos_alumno, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=15)

        # Título del card
        ctk.CTkLabel(
            container,
            text="INFORMACIÓN DEL ESTUDIANTE",
            text_color=TM.warning(),
            font=CTkFont(family="Roboto", size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 10))

        # Grid de datos
        self.fr_datos_grid = ctk.CTkFrame(container, fg_color="transparent")
        self.fr_datos_grid.pack(fill="x")

        # Variables
        self.var_nombre = ctk.StringVar(value="Seleccione un alumno...")
        self.var_dni = ctk.StringVar(value="--")
        self.var_codigo = ctk.StringVar(value="--")

        # Icono
        ctk.CTkLabel(
            self.fr_datos_grid,
            text="👤",
            font=CTkFont(family="Arial", size=28)
        ).grid(row=0, column=0, rowspan=2, padx=(0, 15), pady=5)

        # Nombre
        self.lbl_nombre = ctk.CTkLabel(
            self.fr_datos_grid,
            textvariable=self.var_nombre,
            font=CTkFont(family="Roboto", size=18, weight="bold"),
            text_color=TM.text(),
            anchor="w"
        )
        self.lbl_nombre.grid(row=0, column=1, sticky="w")

        # Subdatos (DNI y Código)
        f_subdatos = ctk.CTkFrame(self.fr_datos_grid, fg_color="transparent")
        f_subdatos.grid(row=1, column=1, sticky="w", pady=(2, 0))

        ctk.CTkLabel(
            f_subdatos,
            text="DNI: ",
            text_color=TM.text_secondary(),
            font=CTkFont(family="Roboto", size=11)
        ).pack(side="left")

        ctk.CTkLabel(
            f_subdatos,
            textvariable=self.var_dni,
            text_color=TM.text(),
            font=CTkFont(family="Roboto", size=11, weight="bold")
        ).pack(side="left")

        ctk.CTkLabel(
            f_subdatos,
            text="  •  CÓDIGO: ",
            text_color=TM.text_secondary(),
            font=CTkFont(family="Roboto", size=11)
        ).pack(side="left")

        ctk.CTkLabel(
            f_subdatos,
            textvariable=self.var_codigo,
            text_color="#f1c40f",
            font=CTkFont(family="Roboto", size=11, weight="bold")
        ).pack(side="left")

    def _crear_tarjetas_kpi(self, parent):
        """Crear tarjetas KPI financieras"""
        fr_resumen = ctk.CTkFrame(parent, fg_color="transparent")
        fr_resumen.pack(fill="x", pady=(0, 15))

        # 3 tarjetas
        self.lbl_val_costo = self._crear_tarjeta(
            fr_resumen, "COSTO TOTAL", "S/. 0.00", "#7f8c8d", "💰"
        )
        self.lbl_val_pagado = self._crear_tarjeta(
            fr_resumen, "TOTAL PAGADO", "S/. 0.00", TM.success(), "✅"
        )
        self.lbl_val_deuda = self._crear_tarjeta(
            fr_resumen, "DEUDA PENDIENTE", "S/. 0.00", TM.danger(), "🚨"
        )

        # Referencias
        self.card_costo = self.lbl_val_costo
        self.card_pagado = self.lbl_val_pagado
        self.card_deuda = self.lbl_val_deuda

    def _crear_tarjeta(self, parent, titulo, valor, color, icono):
        """Crear tarjeta KPI individual"""
        card = ctk.CTkFrame(
            parent,
            fg_color=TM.bg_card(),
            corner_radius=10,
            height=90
        )
        card.pack(side="left", padx=5, expand=True, fill="x")
        card.pack_propagate(False)

        # Barra lateral de color
        bar = ctk.CTkFrame(card, width=5, fg_color=color, corner_radius=0)
        bar.pack(side="left", fill="y")

        # Contenido
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=15, pady=10)

        # Título
        ctk.CTkLabel(
            content,
            text=titulo,
            text_color=TM.text_secondary(),
            font=CTkFont(family="Roboto", size=10, weight="bold")
        ).pack(anchor="w")

        # Valor
        lbl_val = ctk.CTkLabel(
            content,
            text=valor,
            text_color=TM.text(),
            font=CTkFont(family="Roboto", size=22, weight="bold")
        )
        lbl_val.pack(anchor="w", pady=(2, 0))

        # Icono flotante
        ctk.CTkLabel(
            card,
            text=icono,
            font=CTkFont(family="Arial", size=28),
            text_color="#5A5A5A"
        ).pack(side="right", padx=15)

        return lbl_val

    def _crear_caja_pagos(self, parent):
        """Crear sección de caja para registrar pagos"""
        self.fr_caja = ctk.CTkFrame(
            parent,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.fr_caja.pack(fill="x", pady=(0, 15))

        # Header
        h_caja = ctk.CTkFrame(
            self.fr_caja,
            fg_color="#2c3e50",
            height=45,
            corner_radius=10
        )
        h_caja.pack(fill="x", padx=2, pady=2)
        h_caja.pack_propagate(False)

        ctk.CTkLabel(
            h_caja,
            text="💳 REGISTRAR NUEVO ABONO",
            font=CTkFont(family="Roboto", size=13, weight="bold"),
            text_color="white"
        ).pack(side="left", padx=20)

        # Inputs
        fr_inputs = ctk.CTkFrame(self.fr_caja, fg_color="transparent")
        fr_inputs.pack(pady=15, padx=15, fill="x")

        # Monto
        self.entry_monto = ctk.CTkEntry(
            fr_inputs,
            placeholder_text="Monto S/.",
            width=120,
            height=40,
            font=CTkFont(family="Roboto", size=14, weight="bold"),
            justify="center",
            fg_color=TM.bg_panel(),
            border_width=1,
            border_color="#404040",
            text_color=TM.text()
        )
        self.entry_monto.pack(side="left", padx=(0, 10))

        # Concepto
        self.entry_concepto = ctk.CTkEntry(
            fr_inputs,
            placeholder_text="Concepto (Ej: Pensión Marzo)",
            height=40,
            font=CTkFont(family="Roboto", size=12),
            fg_color=TM.bg_panel(),
            border_width=1,
            border_color="#404040",
            text_color=TM.text()
        )
        self.entry_concepto.pack(side="left", padx=(0, 10), fill="x", expand=True)

        # Botón COBRAR
        self.btn_pagar = ctk.CTkButton(
            fr_inputs,
            text="💵 COBRAR",
            fg_color=TM.success(),
            hover_color="#27ae60",
            command=self.realizar_pago,
            state="disabled",
            width=130,
            height=40,
            corner_radius=8,
            font=CTkFont(family="Roboto", size=12, weight="bold")
        )
        self.btn_pagar.pack(side="left", padx=(0, 8))

        # Botón TODO
        self.btn_cobrar_todo = ctk.CTkButton(
            fr_inputs,
            text="TODO",
            fg_color=TM.primary(),
            hover_color="#2980b9",
            width=90,
            height=40,
            corner_radius=8,
            command=self.cobrar_todo,
            state="disabled",
            font=CTkFont(family="Roboto", size=11, weight="bold")
        )
        self.btn_cobrar_todo.pack(side="left")

    def _crear_historial(self, parent):
        """Crear sección de historial de movimientos"""
        # Label título
        ctk.CTkLabel(
            parent,
            text="HISTORIAL DE MOVIMIENTOS",
            font=CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text(),
            anchor="w"
        ).pack(fill="x", pady=(0, 10))

        # Contenedor tabla
        self.fr_tabla_historial = ctk.CTkFrame(
            parent,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.fr_tabla_historial.pack(fill="both", expand=True)

        # Header tabla
        h_hist = ctk.CTkFrame(
            self.fr_tabla_historial,
            height=40,
            fg_color=TM.primary(),
            corner_radius=8
        )
        h_hist.pack(fill="x", padx=5, pady=5)
        h_hist.pack_propagate(False)

        ctk.CTkLabel(
            h_hist,
            text="FECHA",
            width=120,
            text_color="white",
            font=CTkFont(family="Roboto", size=11, weight="bold")
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            h_hist,
            text="CONCEPTO",
            text_color="white",
            font=CTkFont(family="Roboto", size=11, weight="bold"),
            anchor="w"
        ).pack(side="left", padx=10, fill="x", expand=True)

        ctk.CTkLabel(
            h_hist,
            text="MONTO",
            width=120,
            text_color="white",
            font=CTkFont(family="Roboto", size=11, weight="bold")
        ).pack(side="right", padx=15)

        # Cuerpo scrollable
        self.scroll_historial = ctk.CTkScrollableFrame(
            self.fr_tabla_historial,
            fg_color="transparent"
        )
        self.scroll_historial.pack(fill="both", expand=True, padx=5, pady=5)

        # Mensaje vacío inicial
        self._mostrar_estado_vacio_historial()

    def _mostrar_estado_vacio_historial(self):
        """Mostrar estado vacío en historial"""
        empty_frame = ctk.CTkFrame(self.scroll_historial, fg_color="transparent")
        empty_frame.pack(pady=40)

        ctk.CTkLabel(
            empty_frame,
            text="📋",
            font=CTkFont(family="Arial", size=50)
        ).pack()

        ctk.CTkLabel(
            empty_frame,
            text="Sin movimientos registrados",
            font=CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text()
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            empty_frame,
            text="Selecciona un alumno para ver su historial",
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack()

    # ========================================================
    # LÓGICA DEL NEGOCIO
    # ========================================================

    def buscar(self, event=None):
        """Buscar alumnos con debounce"""
        # Cancelar timer anterior
        if self._debounce_timer:
            self.after_cancel(self._debounce_timer)
        
        # Programar nueva búsqueda
        self._debounce_timer = self.after(500, self._ejecutar_busqueda)

    def _ejecutar_busqueda(self):
        """Ejecuta la búsqueda real"""
        criterio = self.entry_busqueda.get()

        # Limpiar resultados
        for widget in self.scroll_resultados.winfo_children():
            widget.destroy()

        resultados = self.controller.buscar_alumno(criterio)

        if not resultados:
            self._mostrar_sin_resultados()
            return

        # Mostrar resultados
        for alu in resultados:
            self._crear_item_resultado(alu)

    def _mostrar_sin_resultados(self):
        """Mostrar mensaje cuando no hay resultados"""
        empty = ctk.CTkFrame(self.scroll_resultados, fg_color="transparent")
        empty.pack(pady=30)

        ctk.CTkLabel(
            empty,
            text="🔍",
            font=CTkFont(family="Arial", size=40)
        ).pack()

        ctk.CTkLabel(
            empty,
            text="Sin resultados",
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text()
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            empty,
            text="Intenta con otro criterio de búsqueda",
            font=CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary()
        ).pack()

    def _crear_item_resultado(self, alumno):
        """Crear item de resultado de búsqueda"""
        nombre = (
            alumno.get("nombre_completo")
            or alumno.get("alumno_nombre")
            or alumno.get("nombre")
            or (
                f"{alumno.get('apellidos', '')}, {alumno.get('nombres', '')}".strip().strip(",")
            )
            or (
                f"{alumno.get('apell_paterno', '')} {alumno.get('apell_materno', '')}, {alumno.get('nombres', '')}".strip().strip(",")
            )
            or "Alumno sin nombre"
        )
        dni = alumno.get("dni", "-")
        alumno_id = alumno.get("id") or alumno.get("alumno_id")

        if not alumno_id:
            return

        # Frame transparente contenedor
        item_frame = ctk.CTkFrame(self.scroll_resultados, fg_color="transparent")
        item_frame.pack(fill="x", pady=1)

        # Botón resultado
        btn = ctk.CTkButton(
            item_frame,
            text=f"{nombre}\n📄 DNI: {dni}",
            fg_color="#2b2b2b",
            hover_color="#404040",
            border_width=0,
            anchor="w",
            height=50,
            text_color=TM.text(),
            font=CTkFont(family="Roboto", size=11),
            corner_radius=8,
            command=lambda a_id=alumno_id: self.seleccionar_alumno(a_id)
        )
        btn.pack(fill="x")

    def seleccionar_alumno(self, id_alumno):
        """Seleccionar un alumno y cargar sus datos"""
        self.alumno_seleccionado_id = id_alumno
        self.btn_pagar.configure(state="normal")
        self.btn_cobrar_todo.configure(state="normal")
        self.actualizar_estado_cuenta()

    def actualizar_estado_cuenta(self):
        """Actualizar UI con estado de cuenta del alumno"""
        datos = self.controller.obtener_estado_cuenta(self.alumno_seleccionado_id)
        if not datos:
            return

        self.deuda_actual_cache = datos["deuda"]

        # 1. Datos alumno
        self.var_nombre.set(datos["nombre_completo"])
        self.var_dni.set(datos["dni"])
        self.var_codigo.set(datos["codigo"])

        # 2. Tarjetas KPI
        self.card_costo.configure(text=f"S/. {datos['costo']:.2f}")
        self.card_pagado.configure(text=f"S/. {datos['pagado']:.2f}")
        self.card_deuda.configure(text=f"S/. {datos['deuda']:.2f}")

        # 3. Historial
        self._cargar_historial(datos["historial"])

    def _cargar_historial(self, historial):
        """Cargar historial de movimientos"""
        # Limpiar
        for w in self.scroll_historial.winfo_children():
            w.destroy()

        if not historial:
            self._mostrar_estado_vacio_historial()
            return

        # Crear filas
        for i, pago in enumerate(historial):
            self._crear_fila_historial(pago, i)

    def _crear_fila_historial(self, pago, index):
        """Crear fila de historial"""
        bg = st.Colors.ROW_ODD if index % 2 == 0 else st.Colors.ROW_EVEN

        row = ctk.CTkFrame(
            self.scroll_historial,
            fg_color=bg,
            corner_radius=6,
            height=40
        )
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        # Fecha
        ctk.CTkLabel(
            row,
            text=pago['fecha'],
            width=120,
            text_color=TM.text(),
            font=CTkFont(family="Roboto Mono", size=10)
        ).pack(side="left", padx=10)

        # Concepto
        ctk.CTkLabel(
            row,
            text=pago['concepto'],
            text_color=TM.text_secondary(),
            font=CTkFont(family="Roboto", size=11),
            anchor="w"
        ).pack(side="left", padx=10, fill="x", expand=True)

        # Monto
        ctk.CTkLabel(
            row,
            text=f"S/. {pago['monto']:.2f}",
            width=120,
            text_color=TM.success(),
            font=CTkFont(family="Roboto", size=11, weight="bold")
        ).pack(side="right", padx=15)

    def cobrar_todo(self):
        """Rellenar inputs con el total de la deuda"""
        if self.deuda_actual_cache <= 0:
            messagebox.showinfo("Información", "El alumno no tiene deuda pendiente.")
            return

        self.entry_monto.delete(0, "end")
        self.entry_monto.insert(0, f"{self.deuda_actual_cache:.2f}")
        self.entry_concepto.delete(0, "end")
        self.entry_concepto.insert(0, "Cancelación Total")

    def realizar_pago(self):
        """Realizar registro de pago"""
        try:
            monto_str = self.entry_monto.get()
            if not monto_str:
                messagebox.showwarning("Validación", "Ingrese un monto")
                return

            monto = float(monto_str)
            concepto = self.entry_concepto.get() or "Pago"

            if monto <= 0:
                messagebox.showwarning("Error", "Monto inválido.")
                return

            if not messagebox.askyesno("Confirmar", f"¿Registrar pago de S/. {monto:.2f}?"):
                return

            exito, msg = self.controller.registrar_pago(
                self.alumno_seleccionado_id, monto, concepto
            )

            if exito:
                messagebox.showinfo("Éxito", msg)
                self.entry_monto.delete(0, "end")
                self.entry_concepto.delete(0, "end")
                self.actualizar_estado_cuenta()
            else:
                messagebox.showerror("Error", msg)

        except ValueError:
            messagebox.showerror("Error", "Monto inválido")
