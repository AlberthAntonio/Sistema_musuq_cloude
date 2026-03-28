"""
Vista de Estado de Cuenta - ESTILO PREMIUM MEJORADO
Sistema Musuq Cloud
Documento de estado de cuenta con búsqueda y visualización tipo papel
"""

import customtkinter as ctk
from tkinter import messagebox
from customtkinter import CTkFont

from controllers.pagos_controller import PagosController
from styles import tabla_style as st
from core.theme_manager import ThemeManager as TM


class EstadoCuentaView(ctk.CTkFrame):
    """
    Vista profesional para estado de cuenta de alumnos.
    Diseño dual: Panel oscuro de búsqueda + Documento blanco de estado
    """

    def __init__(self, parent, auth_client=None):
        super().__init__(parent, fg_color="transparent")

        if not auth_client:
            raise ValueError("auth_client es requerido para inicializar EstadoCuentaView")

        self.auth_client = auth_client
        self.controller = PagosController(auth_client.token)
        self.alumno_seleccionado_id = None
        self._debounce_timer = None  # Timer para debounce

        self.crear_ui()
        self.buscar()

    def crear_ui(self):
        """Crear interfaz completa"""
        # Layout grid: 2 columnas
        self.grid_columnconfigure(0, weight=1, minsize=280)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(0, weight=1)

        # Panel izquierdo: Búsqueda
        self._crear_panel_busqueda()

        # Panel derecho: Documento
        self._crear_panel_documento()

    # ========================================================
    # PANEL IZQUIERDO: BÚSQUEDA (ESTILO DARK)
    # ========================================================

    def _crear_panel_busqueda(self):
        """Crear panel izquierdo con búsqueda de alumnos"""
        self.panel_izq = ctk.CTkFrame(
            self,
            width=280,
            corner_radius=10,
            fg_color=TM.bg_panel()
        )
        self.panel_izq.grid(row=0, column=0, padx=(15, 8), pady=15, sticky="nsew")

        # Header con icono
        self._crear_header_busqueda()

        # Separador
        ctk.CTkFrame(
            self.panel_izq,
            height=2,
            fg_color="#404040"
        ).pack(fill="x", padx=20, pady=15)

        # Buscador
        self._crear_buscador()

        # Lista de resultados
        self._crear_lista_resultados()

    def _crear_header_busqueda(self):
        """Crear header del panel de búsqueda"""
        header = ctk.CTkFrame(self.panel_izq, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 0))

        # Icono grande
        ctk.CTkLabel(
            header,
            text="📊",
            font=CTkFont(family="Arial", size=50)
        ).pack(pady=(0, 10))

        # Título
        ctk.CTkLabel(
            header,
            text="ESTADO DE CUENTA",
            font=CTkFont(family="Roboto", size=16, weight="bold"),
            text_color=TM.text()
        ).pack()

        # Subtítulo
        ctk.CTkLabel(
            header,
            text="Alumno",
            font=CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(pady=(5, 0))

    def _crear_buscador(self):
        """Crear buscador"""
        self.fr_search = ctk.CTkFrame(
            self.panel_izq,
            fg_color=TM.bg_card(),
            height=45,
            corner_radius=10
        )
        self.fr_search.pack(fill="x", padx=15, pady=(0, 10))
        self.fr_search.pack_propagate(False)

        # Icono
        ctk.CTkLabel(
            self.fr_search,
            text="🔍",
            font=CTkFont(family="Arial", size=16),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(15, 8))

        # Entry
        self.entry_busqueda = ctk.CTkEntry(
            self.fr_search,
            placeholder_text="Buscar DNI o Nombre...",
            border_width=0,
            fg_color="transparent",
            text_color=TM.text(),
            font=CTkFont(family="Roboto", size=12)
        )
        self.entry_busqueda.pack(side="left", fill="both", expand=True, padx=(0, 15))
        self.entry_busqueda.bind("<KeyRelease>", self.buscar)

    def _crear_lista_resultados(self):
        """Crear lista scrollable de resultados"""
        self.scroll_lista = ctk.CTkScrollableFrame(
            self.panel_izq,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.scroll_lista.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    # ========================================================
    # PANEL DERECHO: DOCUMENTO (ESTILO PAPEL)
    # ========================================================

    def _crear_panel_documento(self):
        """Crear panel derecho con documento de estado de cuenta"""
        self.panel_doc = ctk.CTkFrame(
            self,
            fg_color="white",
            corner_radius=10
        )
        self.panel_doc.grid(row=0, column=1, padx=(8, 15), pady=15, sticky="nsew")

        # Header documento
        self._crear_header_documento()

        # Datos del estudiante
        self._crear_info_estudiante()

        # Barra de progreso
        self._crear_progreso_pago()

        # Tabla de movimientos
        self._crear_tabla_movimientos()

        # Pie con totales
        self._crear_totales()

    def _crear_header_documento(self):
        """Crear header del documento"""
        fr_header = ctk.CTkFrame(self.panel_doc, fg_color="transparent")
        fr_header.pack(fill="x", padx=35, pady=(25, 15))

        # Título
        ctk.CTkLabel(
            fr_header,
            text="ESTADO DE CUENTA",
            font=CTkFont(family="Arial", size=26, weight="bold"),
            text_color="#2c3e50"
        ).pack(side="left")

        # Botón Imprimir
        self.btn_print = ctk.CTkButton(
            fr_header,
            text="🖨️ Imprimir / PDF",
            fg_color="#2c3e50",
            hover_color="#34495e",
            height=38,
            width=160,
            corner_radius=8,
            font=CTkFont(family="Roboto", size=11, weight="bold"),
            command=self.funcion_pendiente_pdf
        )
        self.btn_print.pack(side="right")

        # Línea divisoria
        ctk.CTkFrame(
            self.panel_doc,
            height=3,
            fg_color="#2c3e50"
        ).pack(fill="x", padx=35, pady=(0, 20))

    def _crear_info_estudiante(self):
        """Crear sección de información del estudiante"""
        self.fr_info = ctk.CTkFrame(
            self.panel_doc,
            fg_color="#f8f9fa",
            corner_radius=8
        )
        self.fr_info.pack(fill="x", padx=35, pady=(0, 20))

        # Container interno
        info_content = ctk.CTkFrame(self.fr_info, fg_color="transparent")
        info_content.pack(fill="x", padx=25, pady=15)

        # Icono + Nombre
        top_row = ctk.CTkFrame(info_content, fg_color="transparent")
        top_row.pack(fill="x", anchor="w")

        ctk.CTkLabel(
            top_row,
            text="👤",
            font=CTkFont(family="Arial", size=24)
        ).pack(side="left", padx=(0, 12))

        self.lbl_nombre = ctk.CTkLabel(
            top_row,
            text="Seleccione un alumno...",
            font=CTkFont(family="Roboto", size=18, weight="bold"),
            text_color="#2c3e50",
            anchor="w"
        )
        self.lbl_nombre.pack(side="left", fill="x", expand=True)

        # Detalles
        self.lbl_detalles = ctk.CTkLabel(
            info_content,
            text="--",
            font=CTkFont(family="Roboto", size=11),
            text_color="#7f8c8d",
            anchor="w"
        )
        self.lbl_detalles.pack(fill="x", pady=(5, 0), padx=(36, 0))

    def _crear_progreso_pago(self):
        """Crear barra de progreso de pago"""
        fr_progreso = ctk.CTkFrame(self.panel_doc, fg_color="transparent")
        fr_progreso.pack(fill="x", padx=35, pady=(0, 20))

        # Header progreso
        h_prog = ctk.CTkFrame(fr_progreso, fg_color="transparent")
        h_prog.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            h_prog,
            text="📈 Progreso de Pago:",
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            text_color="#555"
        ).pack(side="left")

        self.lbl_porcentaje = ctk.CTkLabel(
            h_prog,
            text="0% Pagado",
            font=CTkFont(family="Roboto", size=13, weight="bold"),
            text_color="#27ae60"
        )
        self.lbl_porcentaje.pack(side="right")

        # Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(
            fr_progreso,
            height=14,
            corner_radius=7,
            progress_color="#27ae60",
            fg_color="#e0e0e0"
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x")

    def _crear_tabla_movimientos(self):
        """Crear tabla de movimientos"""
        # Header tabla
        h_tab = ctk.CTkFrame(
            self.panel_doc,
            fg_color="#ecf0f1",
            height=40,
            corner_radius=8
        )
        h_tab.pack(fill="x", padx=35, pady=(0, 0))
        h_tab.pack_propagate(False)

        ctk.CTkLabel(
            h_tab,
            text="FECHA",
            width=110,
            font=CTkFont(family="Roboto", size=11, weight="bold"),
            text_color="#2c3e50"
        ).pack(side="left", padx=15)

        ctk.CTkLabel(
            h_tab,
            text="CONCEPTO",
            font=CTkFont(family="Roboto", size=11, weight="bold"),
            text_color="#2c3e50",
            anchor="w"
        ).pack(side="left", padx=10, expand=True, fill="x")

        ctk.CTkLabel(
            h_tab,
            text="MONTO (S/.)",
            width=120,
            font=CTkFont(family="Roboto", size=11, weight="bold"),
            text_color="#2c3e50"
        ).pack(side="right", padx=20)

        # Cuerpo scrollable
        self.scroll_tabla_doc = ctk.CTkScrollableFrame(
            self.panel_doc,
            fg_color="transparent"
        )
        self.scroll_tabla_doc.pack(fill="both", expand=True, padx=35, pady=(0, 15))

        # Mensaje inicial
        self._mostrar_estado_vacio_tabla()

    def _mostrar_estado_vacio_tabla(self):
        """Mostrar estado vacío en tabla"""
        empty = ctk.CTkFrame(self.scroll_tabla_doc, fg_color="transparent")
        empty.pack(pady=40)

        ctk.CTkLabel(
            empty,
            text="📋",
            font=CTkFont(family="Arial", size=50)
        ).pack()

        ctk.CTkLabel(
            empty,
            text="Sin movimientos registrados",
            font=CTkFont(family="Roboto", size=13, weight="bold"),
            text_color="#2c3e50"
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            empty,
            text="Selecciona un alumno para ver su estado de cuenta",
            font=CTkFont(family="Roboto", size=11),
            text_color="#7f8c8d"
        ).pack()

    def _crear_totales(self):
        """Crear sección de totales"""
        fr_totales = ctk.CTkFrame(
            self.panel_doc,
            fg_color="#f4f6f7",
            height=70,
            corner_radius=8
        )
        fr_totales.pack(fill="x", padx=35, pady=(0, 25))
        fr_totales.pack_propagate(False)

        # Container interno
        totales_content = ctk.CTkFrame(fr_totales, fg_color="transparent")
        totales_content.pack(expand=True, fill="both", padx=25)

        # Total Pagado
        self.lbl_total_pagado = ctk.CTkLabel(
            totales_content,
            text="PAGADO: S/. 0.00",
            font=CTkFont(family="Roboto", size=16, weight="bold"),
            text_color="#27ae60"
        )
        self.lbl_total_pagado.pack(side="right", padx=15)

        # Separador
        ctk.CTkLabel(
            totales_content,
            text="│",
            font=CTkFont(family="Arial", size=20),
            text_color="#bdc3c7"
        ).pack(side="right", padx=10)

        # Deuda Total
        self.lbl_total_deuda = ctk.CTkLabel(
            totales_content,
            text="DEUDA TOTAL: S/. 0.00",
            font=CTkFont(family="Roboto", size=16, weight="bold"),
            text_color="#c0392b"
        )
        self.lbl_total_deuda.pack(side="right", padx=15)

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

        # Limpiar lista
        for item in self.scroll_lista.winfo_children():
            item.destroy()

        resultados = self.controller.buscar_alumno(criterio)

        if not resultados:
            self._mostrar_sin_resultados()
            return

        # Mostrar resultados
        for alu in resultados:
            self._crear_item_resultado(alu)

    def _mostrar_sin_resultados(self):
        """Mostrar mensaje cuando no hay resultados"""
        empty = ctk.CTkFrame(self.scroll_lista, fg_color="transparent")
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
            text="Intenta con otro criterio",
            font=CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary()
        ).pack()

    def _crear_item_resultado(self, alumno):
        """Crear item de resultado"""
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

        item_frame = ctk.CTkFrame(self.scroll_lista, fg_color="transparent")
        item_frame.pack(fill="x", pady=1)

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
            command=lambda a_id=alumno_id: self.cargar_estado_cuenta(a_id)
        )
        btn.pack(fill="x")

    def cargar_estado_cuenta(self, id_alumno):
        """Cargar estado de cuenta del alumno"""
        self.alumno_seleccionado_id = id_alumno
        datos = self.controller.obtener_estado_cuenta(id_alumno)

        if not datos:
            return

        # 1. Info Header
        self.lbl_nombre.configure(text=datos['nombre_completo'])
        self.lbl_detalles.configure(
            text=f"DNI: {datos['dni']}  •  Código: {datos['codigo']}  •  {datos.get('info_extra', '')}"
        )

        # 2. Barra de Progreso
        self._actualizar_progreso(datos['costo'], datos['pagado'])

        # 3. Tabla
        self._cargar_tabla_movimientos(datos['historial'])

        # 4. Totales
        self.lbl_total_pagado.configure(text=f"PAGADO: S/. {datos['pagado']:.2f}")
        self.lbl_total_deuda.configure(text=f"DEUDA TOTAL: S/. {datos['deuda']:.2f}")

    def _actualizar_progreso(self, costo, pagado):
        """Actualizar barra de progreso"""
        if costo > 0:
            porcentaje = min(pagado / costo, 1.0)
        else:
            porcentaje = 1.0 if pagado > 0 else 0.0

        self.progress_bar.set(porcentaje)
        self.lbl_porcentaje.configure(text=f"{porcentaje*100:.0f}% Pagado")

    def _cargar_tabla_movimientos(self, historial):
        """Cargar movimientos en la tabla"""
        # Limpiar
        for w in self.scroll_tabla_doc.winfo_children():
            w.destroy()

        if not historial:
            self._mostrar_estado_vacio_tabla()
            return

        # Crear filas
        for i, pago in enumerate(historial):
            self._crear_fila_movimiento(pago, i)

    def _crear_fila_movimiento(self, pago, index):
        """Crear fila de movimiento"""
        bg_row = "white" if index % 2 == 0 else "#fcfcfc"

        row = ctk.CTkFrame(
            self.scroll_tabla_doc,
            fg_color=bg_row,
            corner_radius=0,
            height=38
        )
        row.pack(fill="x")
        row.pack_propagate(False)

        # Fecha
        ctk.CTkLabel(
            row,
            text=pago['fecha'],
            width=110,
            text_color="#555",
            font=CTkFont(family="Roboto Mono", size=10)
        ).pack(side="left", padx=15)

        # Concepto
        ctk.CTkLabel(
            row,
            text=pago['concepto'],
            text_color="#333",
            font=CTkFont(family="Roboto", size=11),
            anchor="w"
        ).pack(side="left", padx=10, expand=True, fill="x")

        # Monto
        ctk.CTkLabel(
            row,
            text=f"S/. {pago['monto']:.2f}",
            width=120,
            text_color="#27ae60",
            font=CTkFont(family="Roboto", size=11, weight="bold")
        ).pack(side="right", padx=20)

        # Línea separadora
        ctk.CTkFrame(
            self.scroll_tabla_doc,
            height=1,
            fg_color="#eeeeee"
        ).pack(fill="x")

    def funcion_pendiente_pdf(self):
        """Función para generar PDF"""
        if not self.alumno_seleccionado_id:
            messagebox.showwarning("Advertencia", "Seleccione un alumno primero")
            return
        messagebox.showinfo("Próximamente", "Función de impresión/PDF en desarrollo")
