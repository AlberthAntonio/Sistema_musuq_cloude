"""
Vista de Gestión de Docentes - ESTILO MEJORADO
Sistema Musuq Cloud
Formulario de registro + Tabla de listado con filtros y búsqueda
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import date
from typing import Dict, Any

from controllers.docentes_controller import DocentesController
from styles import tabla_style as st
from core.theme_manager import ThemeManager as TM
#from ui.views.docentes.resumen_docentes_view import ResumenDocenteView


class GestionDocentesView(ctk.CTkFrame):
    """Vista de gestión de docentes con diseño profesional"""

    def __init__(self, parent, auth_client=None):
        super().__init__(parent, fg_color="transparent")
        self.controller = DocentesController(auth_client.token if auth_client else "")

        # Variables de estado
        self.docente_seleccionado_id = None
        self.docente_seleccionado_data = None

        # Layout principal (formulario + tabla)
        self.grid_columnconfigure(0, weight=1)  # Formulario
        self.grid_columnconfigure(1, weight=2)  # Tabla
        self.grid_rowconfigure(0, weight=1)

        self.create_widgets()

    def create_widgets(self):
        # ============================
        # PANEL IZQUIERDO: FORMULARIO
        # ============================
        self.panel_form = ctk.CTkScrollableFrame(
            self,
            width=420,
            fg_color=TM.bg_card(),
            corner_radius=0
        )
        self.panel_form.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")

        # Header del formulario
        header_form = ctk.CTkFrame(self.panel_form, fg_color="transparent")
        header_form.pack(pady=(15, 20), padx=15)

        ctk.CTkLabel(
            header_form,
            text="👨‍🏫",
            font=ctk.CTkFont(family="Arial", size=40)
        ).pack()

        ctk.CTkLabel(
            header_form,
            text="FICHA DE DOCENTE",
            font=ctk.CTkFont(family="Roboto", size=18, weight="bold"),
            text_color=TM.text()
        ).pack(pady=(5, 0))

        # Separador
        ctk.CTkFrame(
            self.panel_form,
            height=2,
            fg_color=TM.bg_panel()
        ).pack(fill="x", padx=20, pady=(0, 15))

        # --- SECCIÓN 1: DATOS PERSONALES ---
        self.seccion(self.panel_form, "1. DATOS PERSONALES")
        self.entry_dni = self.campo(self.panel_form, "DNI *", solo_numeros=True, max_char=8)
        self.entry_nombres = self.campo(self.panel_form, "Nombres *")
        self.entry_ape_pat = self.campo(self.panel_form, "Ap. Paterno *")
        self.entry_ape_mat = self.campo(self.panel_form, "Ap. Materno *")
        self.entry_celular = self.campo(self.panel_form, "Celular", solo_numeros=True, max_char=9)
        self.entry_email = self.campo(self.panel_form, "Email")

        # --- SECCIÓN 2: DATOS LABORALES ---
        self.seccion(self.panel_form, "2. INFORMACIÓN LABORAL")

        self.combo_especialidad = self.combo(
            self.panel_form,
            "Especialidad",
            ["Matemáticas", "Comunicación", "Ciencias Naturales", "Ciencias Sociales",
             "Inglés", "Educación Física", "Arte", "Computación"]
        )

        self.combo_tipo_contrato = self.combo(
            self.panel_form,
            "Tipo Contrato",
            ["Nombrado", "Contratado", "Por Horas"]
        )

        self.combo_turno = self.combo(
            self.panel_form,
            "Turno",
            ["MAÑANA", "TARDE", "AMBOS TURNOS"]
        )

        # Fecha de ingreso
        fr_fecha = ctk.CTkFrame(self.panel_form, fg_color="transparent")
        fr_fecha.pack(fill="x", pady=5, padx=15)

        ctk.CTkLabel(
            fr_fecha,
            text="Fecha Ingreso",
            width=120,
            anchor="w",
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=5)

        self.lbl_fecha = ctk.CTkLabel(
            fr_fecha,
            text=date.today().strftime("%d/%m/%Y"),
            font=ctk.CTkFont(family="Roboto Mono", size=11, weight="bold"),
            text_color=TM.text()
        )
        self.lbl_fecha.pack(side="left", padx=5)

        # --- ESTADO ---
        switch_container = ctk.CTkFrame(self.panel_form, fg_color="transparent")
        switch_container.pack(pady=15, padx=15)

        self.switch_activo = ctk.CTkSwitch(
            switch_container,
            text="Docente Activo",
            progress_color=TM.success(),
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text()
        )
        self.switch_activo.pack()
        self.switch_activo.select()

        # --- BOTONES ---
        fr_btns = ctk.CTkFrame(self.panel_form, fg_color="transparent")
        fr_btns.pack(fill="x", pady=(15, 20), padx=15)

        self.btn_guardar = ctk.CTkButton(
            fr_btns,
            text="💾 GUARDAR DOCENTE",
            fg_color=TM.success(),
            hover_color="#27ae60",
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            command=self.guardar_docente
        )
        self.btn_guardar.pack(fill="x", pady=(0, 8))

        self.btn_limpiar = ctk.CTkButton(
            fr_btns,
            text="🧹 LIMPIAR FORMULARIO",
            fg_color="#404040",
            hover_color="#505050",
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            command=self.limpiar_formulario
        )
        self.btn_limpiar.pack(fill="x")

        # ============================
        # PANEL DERECHO: TABLA
        # ============================
        self.panel_tabla = ctk.CTkFrame(self, fg_color="transparent")
        self.panel_tabla.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")

        # Header con título
        fr_header = ctk.CTkFrame(
            self.panel_tabla,
            fg_color=TM.bg_card(),
            height=70,
            corner_radius=10
        )
        fr_header.pack(fill="x", pady=(0, 15))
        fr_header.pack_propagate(False)

        header_content = ctk.CTkFrame(fr_header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(
            header_content,
            text="👥 LISTA DE DOCENTES",
            font=ctk.CTkFont(family="Roboto", size=18, weight="bold"),
            text_color=TM.text()
        ).pack(side="left")

        # Botón para ver resumen del docente seleccionado
        ctk.CTkButton(
            header_content,
            text="👁 Ver resumen",
            fg_color=TM.primary(),
            hover_color="#2980b9",
            width=140,
            height=34,
            corner_radius=8,
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            command=self.ver_resumen_docente
        ).pack(side="right")

        # --- BUSCADOR MEJORADO ---
        fr_search = ctk.CTkFrame(
            self.panel_tabla,
            fg_color=TM.bg_card(),
            corner_radius=10,
            height=50
        )
        fr_search.pack(fill="x", pady=(0, 15))
        fr_search.pack_propagate(False)

        search_content = ctk.CTkFrame(fr_search, fg_color="transparent")
        search_content.pack(fill="both", expand=True, padx=15, pady=8)

        ctk.CTkLabel(
            search_content,
            text="🔍",
            font=ctk.CTkFont(family="Arial", size=16),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(5, 10))

        self.entry_buscar = ctk.CTkEntry(
            search_content,
            placeholder_text="Buscar por DNI, nombre o especialidad...",
            border_width=0,
            fg_color=TM.bg_panel(),
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=TM.text()
        )
        self.entry_buscar.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry_buscar.bind("<KeyRelease>", self.buscar_docente)

        # --- FILTROS MEJORADOS ---
        fr_filtros = ctk.CTkFrame(
            self.panel_tabla,
            fg_color=TM.bg_card(),
            corner_radius=10,
            height=50
        )
        fr_filtros.pack(fill="x", pady=(0, 15))
        fr_filtros.pack_propagate(False)

        filtros_content = ctk.CTkFrame(fr_filtros, fg_color="transparent")
        filtros_content.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(
            filtros_content,
            text="Filtrar:",
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(0, 15))

        self.radio_var = ctk.StringVar(value="todos")

        radio_style = {
            "font": ctk.CTkFont(family="Roboto", size=11),
            "text_color": TM.text(),
            "fg_color": TM.primary(),
            "hover_color": "#2980b9"
        }

        ctk.CTkRadioButton(
            filtros_content,
            text="✅ Activos",
            variable=self.radio_var,
            value="activos",
            command=self.filtrar_tabla,
            **radio_style
        ).pack(side="left", padx=8)

        ctk.CTkRadioButton(
            filtros_content,
            text="❌ Inactivos",
            variable=self.radio_var,
            value="inactivos",
            command=self.filtrar_tabla,
            **radio_style
        ).pack(side="left", padx=8)

        ctk.CTkRadioButton(
            filtros_content,
            text="📋 Todos",
            variable=self.radio_var,
            value="todos",
            command=self.filtrar_tabla,
            **radio_style
        ).pack(side="left", padx=8)

        # --- CONTENEDOR TABLA ---
        self.container_tabla = ctk.CTkFrame(
            self.panel_tabla,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.container_tabla.pack(fill="both", expand=True)

        # Cabecera
        self.crear_cabecera()

        # Cuerpo scrollable
        self.scroll_tabla = ctk.CTkScrollableFrame(
            self.container_tabla,
            fg_color="transparent"
        )
        self.scroll_tabla.pack(fill="both", expand=True, padx=5, pady=5)

        # --- FOOTER CON CONTADOR ---
        fr_footer = ctk.CTkFrame(self.panel_tabla, fg_color="transparent")
        fr_footer.pack(fill="x", pady=(10, 0))

        self.lbl_contador = ctk.CTkLabel(
            fr_footer,
            text="Total: 0 docentes",
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        )
        self.lbl_contador.pack(side="left")

        # Cargar datos
        self.cargar_tabla()

    # =================== MÉTODOS UI HELPERS ===================

    def seccion(self, parent, titulo):
        """Título de sección con diseño mejorado"""
        seccion_frame = ctk.CTkFrame(parent, fg_color="transparent")
        seccion_frame.pack(fill="x", pady=(15, 10), padx=15)

        ctk.CTkLabel(
            seccion_frame,
            text=titulo,
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.primary(),
            anchor="w"
        ).pack(side="left")

        # Línea decorativa
        ctk.CTkFrame(
            seccion_frame,
            height=2,
            fg_color=TM.primary()
        ).pack(side="left", fill="x", expand=True, padx=(10, 0))

    def campo(self, parent, label, solo_numeros=False, max_char=None):
        """Campo de entrada estándar mejorado"""
        fr = ctk.CTkFrame(parent, fg_color="transparent")
        fr.pack(fill="x", pady=3, padx=15)

        ctk.CTkLabel(
            fr,
            text=label,
            width=120,
            anchor="w",
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=5)

        entry = ctk.CTkEntry(
            fr,
            fg_color=TM.bg_panel(),
            border_width=0,
            corner_radius=8,
            height=35,
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=TM.text()
        )

        if solo_numeros or max_char:
            vcmd = self.register(lambda P: self.validar_input(P, solo_numeros, max_char))
            entry.configure(validate="key", validatecommand=(vcmd, '%P'))

        entry.pack(side="left", fill="x", expand=True, padx=5)
        entry.bind("<FocusOut>", lambda e: self.mayusculas(entry))

        return entry

    def combo(self, parent, label, valores):
        """ComboBox estándar mejorado"""
        fr = ctk.CTkFrame(parent, fg_color="transparent")
        fr.pack(fill="x", pady=3, padx=15)

        ctk.CTkLabel(
            fr,
            text=label,
            width=120,
            anchor="w",
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=5)

        combo = ctk.CTkComboBox(
            fr,
            values=valores,
            state="readonly",
            fg_color=TM.bg_panel(),
            border_width=0,
            button_color=TM.primary(),
            button_hover_color="#2980b9",
            dropdown_fg_color=TM.bg_panel(),
            font=ctk.CTkFont(family="Roboto", size=11),
            dropdown_font=ctk.CTkFont(family="Roboto", size=10)
        )
        combo.set("-- Seleccione --")
        combo.pack(side="left", fill="x", expand=True, padx=5)

        return combo

    def validar_input(self, texto, solo_numeros, max_char):
        """Validación de entrada"""
        if max_char and len(texto) > max_char:
            return False
        if solo_numeros:
            return texto.isdigit() or texto == ""
        return True

    def mayusculas(self, entry):
        """Convertir a mayúsculas"""
        if entry.cget("state") != "disabled":
            pos = entry.index("insert")
            texto = entry.get().upper()
            entry.delete(0, 'end')
            entry.insert(0, texto)
            entry.icursor(pos)

    def crear_cabecera(self):
        """Crear cabecera de tabla con diseño mejorado"""
        header = ctk.CTkFrame(
            self.container_tabla,
            height=40,
            fg_color=st.Colors.TABLE_HEADER,
            corner_radius=5
        )
        header.pack(fill="x", padx=5, pady=(5, 0))

        columnas = [
            ("DNI", 100),
            ("DOCENTE", 250),
            ("ESPECIALIDAD", 150),
            ("CURSOS", 200),
            ("ESTADO", 80)
        ]

        for titulo, ancho in columnas:
            ctk.CTkLabel(
                header,
                text=titulo,
                font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
                text_color="white",
                width=ancho
            ).pack(side="left", padx=2)

    def cargar_tabla(self):
        """Cargar datos usando controller"""
        # Limpiar tabla
        for w in self.scroll_tabla.winfo_children():
            w.destroy()

        criterio = self.entry_buscar.get().strip()
        filtro = self.radio_var.get()

        resultados = self.controller.obtener_docentes(criterio, filtro)

        if not resultados:
            # Estado vacío
            empty_state = ctk.CTkFrame(self.scroll_tabla, fg_color="transparent")
            empty_state.pack(fill="both", expand=True, pady=60)

            ctk.CTkLabel(
                empty_state,
                text="📭",
                font=ctk.CTkFont(family="Arial", size=60)
            ).pack(pady=10)

            ctk.CTkLabel(
                empty_state,
                text="No se encontraron docentes",
                font=ctk.CTkFont(family="Roboto", size=16, weight="bold"),
                text_color=TM.text()
            ).pack()

            ctk.CTkLabel(
                empty_state,
                text="Intente con otro criterio de búsqueda",
                font=ctk.CTkFont(family="Roboto", size=12),
                text_color=TM.text_secondary()
            ).pack(pady=(5, 0))
        else:
            for i, d in enumerate(resultados):
                self.crear_fila(i, d)

        self.lbl_contador.configure(text=f"Total: {len(resultados)} docentes")

    def crear_fila(self, idx, data):
        """Crear fila en tabla con diseño mejorado"""
        # Colores consistentes
        bg = "#2d2d2d" if idx % 2 == 0 else "#363636"

        row = ctk.CTkFrame(
            self.scroll_tabla,
            fg_color=bg,
            corner_radius=5,
            height=40
        )
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        # Interactividad mejorada
        def on_enter(e):
            row.configure(fg_color="#34495e")

        def on_leave(e):
            row.configure(fg_color=bg)

        def on_click(e):
            self.seleccionar_fila(row, data)

        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)
        row.bind("<Button-1>", on_click)

        font_regular = ctk.CTkFont(family="Roboto", size=11)
        font_mono = ctk.CTkFont(family="Roboto Mono", size=11, weight="bold")

        # Columnas
        # DNI
        ctk.CTkLabel(
            row,
            text=data['dni'],
            width=100,
            text_color=TM.text_secondary(),
            font=font_mono
        ).pack(side="left", padx=2)

        # Nombre
        ctk.CTkLabel(
            row,
            text=data['nombre'],
            width=250,
            anchor="w",
            text_color=TM.text(),
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold")
        ).pack(side="left", padx=2)

        # Especialidad
        ctk.CTkLabel(
            row,
            text=data['especialidad'],
            width=150,
            text_color=TM.text_secondary(),
            font=font_regular
        ).pack(side="left", padx=2)

        # Cursos
        cursos_txt = data['cursos']
        if len(cursos_txt) > 30:
            cursos_txt = cursos_txt[:27] + "..."

        ctk.CTkLabel(
            row,
            text=cursos_txt,
            width=200,
            anchor="w",
            text_color=TM.text_secondary(),
            font=font_regular
        ).pack(side="left", padx=2)

        # Badge de estado mejorado
        es_activo = "Activo" in data['estado']
        color_estado = TM.success() if es_activo else TM.danger()

        badge = ctk.CTkLabel(
            row,
            text=data['estado'],
            width=80,
            fg_color=color_estado,
            corner_radius=5,
            text_color="white",
            font=ctk.CTkFont(family="Roboto", size=9, weight="bold")
        )
        badge.pack(side="left", padx=2)

        # Bind recursivo a todos los widgets
        for widget in row.winfo_children():
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)

    def seleccionar_fila(self, row, data):
        """Seleccionar fila de la tabla y recordar el docente activo."""
        self.docente_seleccionado_id = data.get("id")
        self.docente_seleccionado_data = data

    def ver_resumen_docente(self):
        """Abrir la ventana de resumen para el docente seleccionado."""
        if not self.docente_seleccionado_data:
            messagebox.showwarning(
                "Resumen de docente",
                "Primero seleccione un docente de la tabla."
            )
            return

        d = self.docente_seleccionado_data

        info = {
            "nombre_completo": d.get("nombre_completo") or d.get("nombre"),
            "dni": d.get("dni"),
            "especialidad": d.get("especialidad"),
            # Estos campos se llenarán cuando la API los proporcione
            "turno": None,
            "tipo_contrato": None,
            "celular": d.get("celular"),
            "email": d.get("email"),
        }

        ResumenDocenteView(self, docente=info)

    # =================== MÉTODOS DE LÓGICA ===================

    def guardar_docente(self):
        """Validar y guardar docente"""
        dni = self.entry_dni.get().strip()
        nombres = self.entry_nombres.get().strip()
        ape_pat = self.entry_ape_pat.get().strip()

        # Validaciones
        if not dni or len(dni) != 8:
            messagebox.showwarning("Validación", "DNI debe tener exactamente 8 dígitos")
            self.entry_dni.focus()
            return

        if not nombres or not ape_pat:
            messagebox.showwarning("Validación", "Complete los campos obligatorios marcados con *")
            return

        # Preparar datos
        datos = {
            "dni": dni,
            "nombres": nombres,
            "paterno": ape_pat,
            "materno": self.entry_ape_mat.get().strip(),
            "celular": self.entry_celular.get().strip(),
            "email": self.entry_email.get().strip(),
            "especialidad": self.combo_especialidad.get(),
            "tipo_contrato": self.combo_tipo_contrato.get(),
            "turno": self.combo_turno.get(),
            "activo": self.switch_activo.get()
        }

        # Guardar
        exito, msg = self.controller.guardar_docente(datos)

        if exito:
            messagebox.showinfo("✅ Éxito", msg)
            self.limpiar_formulario()
            self.cargar_tabla()
        else:
            messagebox.showerror("❌ Error", msg)

    def limpiar_formulario(self):
        """Limpiar todos los campos del formulario"""
        self.entry_dni.delete(0, 'end')
        self.entry_nombres.delete(0, 'end')
        self.entry_ape_pat.delete(0, 'end')
        self.entry_ape_mat.delete(0, 'end')
        self.entry_celular.delete(0, 'end')
        self.entry_email.delete(0, 'end')

        self.combo_especialidad.set("-- Seleccione --")
        self.combo_tipo_contrato.set("-- Seleccione --")
        self.combo_turno.set("-- Seleccione --")
        self.switch_activo.select()
        self.docente_seleccionado_id = None

        # Focus al primer campo
        self.entry_dni.focus()

    def buscar_docente(self, event):
        """Búsqueda en tiempo real"""
        self.cargar_tabla()

    def filtrar_tabla(self):
        """Aplicar filtro a la tabla"""
        self.cargar_tabla()
