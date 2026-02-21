# app/ui/admin_gestion_docentes_view.py
import customtkinter as ctk
from tkinter import messagebox
from datetime import date
import app.styles.tabla_style as st

class GestionDocentesView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        # self.controller = DocenteController()  # ← Después
        
        # Variables de estado
        self.docente_seleccionado_id = None
        self.cursos_disponibles = []  # Cargar de BD después
        
        self.configure(fg_color=st.Colors.BG_MAIN)
        
        # Layout principal (70% tabla, 30% formulario)
        self.grid_columnconfigure(0, weight=1)  # Formulario
        self.grid_columnconfigure(1, weight=2)  # Tabla
        self.grid_rowconfigure(0, weight=1)
        
        # ============================
        # PANEL IZQUIERDO: FORMULARIO
        # ============================
        self.panel_form = ctk.CTkScrollableFrame(
            self, 
            width=400,
            label_text="📋 FICHA DE DOCENTE",
            label_font=st.Fonts.TITLE
        )
        self.panel_form.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        
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
            ["Mañana", "Tarde", "Ambos Turnos"]
        )
        
        fr_fecha = ctk.CTkFrame(self.panel_form, fg_color="transparent")
        fr_fecha.pack(fill="x", pady=2)
        ctk.CTkLabel(fr_fecha, text="Fecha Ingreso", width=120, anchor="w").pack(side="left", padx=5)
        self.lbl_fecha = ctk.CTkLabel(fr_fecha, text=date.today().strftime("%d/%m/%Y"))
        self.lbl_fecha.pack(side="left", padx=5)
        
        # --- SECCIÓN 3: CURSOS ASIGNADOS ---
        self.seccion(self.panel_form, "3. CURSOS A CARGO")
        
        self.frame_cursos = ctk.CTkScrollableFrame(
            self.panel_form, 
            fg_color="#2b2b2b",
            height=200
        )
        self.frame_cursos.pack(fill="both", expand=True, padx=15, pady=5)
        
        # Checkboxes de cursos (cargar dinámicamente después)
        self.checkbox_cursos = {}
        self.cargar_cursos_dummy()  # Temporal
        
        # --- ESTADO ---
        self.switch_activo = ctk.CTkSwitch(
            self.panel_form,
            text="Docente Activo",
            progress_color=st.Colors.PUNTUAL
        )
        self.switch_activo.pack(pady=10)
        self.switch_activo.select()
        
        # --- BOTONES ---
        fr_btns = ctk.CTkFrame(self.panel_form, fg_color="transparent")
        fr_btns.pack(fill="x", pady=20, padx=15)
        
        self.btn_guardar = ctk.CTkButton(
            fr_btns,
            text="💾 GUARDAR",
            fg_color=st.Colors.ASISTENCIA,
            hover_color="#2980b9",
            height=40,
            command=self.guardar_docente
        )
        self.btn_guardar.pack(fill="x", pady=5)
        
        self.btn_limpiar = ctk.CTkButton(
            fr_btns,
            text="🧹 LIMPIAR",
            fg_color="#404040",
            hover_color="#505050",
            height=35,
            command=self.limpiar_formulario
        )
        self.btn_limpiar.pack(fill="x", pady=5)
        
        # ============================
        # PANEL DERECHO: TABLA
        # ============================
        self.panel_tabla = ctk.CTkFrame(self, fg_color="transparent")
        self.panel_tabla.grid(row=0, column=1, padx=(5, 10), pady=(15, 5), sticky="nsew")
        
        # Header
        fr_header = ctk.CTkFrame(self.panel_tabla, fg_color="transparent")
        fr_header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            fr_header, 
            text="LISTA DE DOCENTES",
            font=("Roboto", 14, "bold"),
            text_color="white"
        ).pack(side="left")
        
        # Buscador
        fr_search = ctk.CTkFrame(self.panel_tabla, fg_color="#383838", corner_radius=20, height=40)
        fr_search.pack(fill="x", pady=(0, 10))
        fr_search.pack_propagate(False)
        
        ctk.CTkLabel(fr_search, text="🔍", font=("Arial", 14)).pack(side="left", padx=10)
        
        self.entry_buscar = ctk.CTkEntry(
            fr_search,
            placeholder_text="Buscar por DNI, nombre...",
            border_width=0,
            fg_color="transparent"
        )
        self.entry_buscar.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_buscar.bind("<KeyRelease>", self.buscar_docente)
        
        # Filtros
        fr_filtros = ctk.CTkFrame(self.panel_tabla, fg_color="transparent")
        fr_filtros.pack(fill="x", pady=(0, 10))
        
        self.radio_var = ctk.StringVar(value="activos")
        
        ctk.CTkRadioButton(
            fr_filtros, text="✅ Activos", variable=self.radio_var, 
            value="activos", command=self.filtrar_tabla
        ).pack(side="left", padx=5)
        
        ctk.CTkRadioButton(
            fr_filtros, text="❌ Inactivos", variable=self.radio_var,
            value="inactivos", command=self.filtrar_tabla
        ).pack(side="left", padx=5)
        
        ctk.CTkRadioButton(
            fr_filtros, text="📋 Todos", variable=self.radio_var,
            value="todos", command=self.filtrar_tabla
        ).pack(side="left", padx=5)
        
        # Contenedor tabla
        self.container_tabla = ctk.CTkFrame(self.panel_tabla, fg_color="#2b2b2b", corner_radius=10)
        self.container_tabla.pack(fill="both", expand=True)
        
        # Cabecera
        self.crear_cabecera()
        
        # Cuerpo scrollable
        self.scroll_tabla = ctk.CTkScrollableFrame(self.container_tabla, fg_color="transparent")
        self.scroll_tabla.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Footer con contador
        self.lbl_contador = ctk.CTkLabel(
            self.panel_tabla,
            text="Total: 0 docentes",
            text_color="gray"
        )
        self.lbl_contador.pack(pady=5)
        
        # Cargar datos dummy
        self.cargar_tabla_dummy()
    
    # =================== MÉTODOS UI HELPERS ===================
    
    def seccion(self, parent, titulo):
        """Título de sección"""
        ctk.CTkLabel(
            parent, 
            text=titulo,
            font=("Roboto", 12, "bold"),
            text_color=st.Colors.ASISTENCIA
        ).pack(pady=(15, 5), anchor="w", padx=15)
    
    def campo(self, parent, label, solo_numeros=False, max_char=None):
        """Campo de entrada estándar"""
        fr = ctk.CTkFrame(parent, fg_color="transparent")
        fr.pack(fill="x", pady=2)
        
        ctk.CTkLabel(fr, text=label, width=120, anchor="w").pack(side="left", padx=5)
        
        entry = ctk.CTkEntry(fr)
        
        if solo_numeros or max_char:
            vcmd = self.register(lambda P: self.validar_input(P, solo_numeros, max_char))
            entry.configure(validate="key", validatecommand=(vcmd, '%P'))
        
        entry.pack(side="left", fill="x", expand=True, padx=5)
        entry.bind("<KeyRelease>", lambda e: self.mayusculas(entry))
        
        return entry
    
    def combo(self, parent, label, valores):
        """ComboBox estándar"""
        fr = ctk.CTkFrame(parent, fg_color="transparent")
        fr.pack(fill="x", pady=2)
        
        ctk.CTkLabel(fr, text=label, width=120, anchor="w").pack(side="left", padx=5)
        
        combo = ctk.CTkComboBox(fr, values=valores, state="readonly")
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
        """Convertir a mayúsculas en tiempo real"""
        if entry.cget("state") != "disabled":
            pos = entry.index("insert")
            texto = entry.get().upper()
            entry.delete(0, 'end')
            entry.insert(0, texto)
            entry.icursor(pos)
    
    def crear_cabecera(self):
        """Crear header de tabla"""
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
                font=("Roboto", 11, "bold"),
                text_color="white",
                width=ancho
            ).pack(side="left", padx=2)
    
    def cargar_cursos_dummy(self):
        """Cargar checkboxes de cursos (temporal)"""
        cursos_ejemplo = [
            "Aritmética", "Álgebra", "Geometría", "Trigonometría",
            "Física", "Química", "Biología", "Razonamiento Verbal",
            "Razonamiento Matemático", "Historia", "Geografía"
        ]
        
        for curso in cursos_ejemplo:
            var = ctk.BooleanVar()
            chk = ctk.CTkCheckBox(
                self.frame_cursos,
                text=curso,
                variable=var,
                fg_color=st.Colors.ASISTENCIA,
                hover_color="#2980b9"
            )
            chk.pack(anchor="w", padx=10, pady=2)
            self.checkbox_cursos[curso] = var
    
    def cargar_tabla_dummy(self):
        """Cargar datos de ejemplo"""
        docentes_ejemplo = [
            ("43210987", "PÉREZ GÓMEZ, Juan", "Matemáticas", "Aritmética, Álgebra", "✅ Activo"),
            ("41234567", "LÓPEZ RAMÍREZ, María", "Comunicación", "R. Verbal, Literatura", "✅ Activo"),
            ("45678901", "TORRES SILVA, Carlos", "Ciencias", "Física, Química", "❌ Inactivo"),
        ]
        
        for i, (dni, nombre, esp, cursos, estado) in enumerate(docentes_ejemplo):
            self.crear_fila(i, dni, nombre, esp, cursos, estado)
        
        self.lbl_contador.configure(text=f"Total: {len(docentes_ejemplo)} docentes")
    
    def crear_fila(self, idx, dni, nombre, especialidad, cursos, estado):
        """Crear fila en tabla"""
        bg = st.Colors.ROW_ODD if idx % 2 == 0 else st.Colors.ROW_EVEN
        
        row = ctk.CTkFrame(self.scroll_tabla, fg_color=bg, corner_radius=5, height=40)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        
        # Interactividad
        def on_click(e):
            self.seleccionar_fila(row, dni)
        
        def on_enter(e):
            row.configure(fg_color="#3a3a3a")
        
        def on_leave(e):
            row.configure(fg_color=bg)
        
        row.bind("<Button-1>", on_click)
        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)
        
        # Columnas
        ctk.CTkLabel(row, text=dni, width=100, text_color="gray").pack(side="left", padx=2)
        ctk.CTkLabel(row, text=nombre, width=250, anchor="w", text_color="white").pack(side="left", padx=2)
        ctk.CTkLabel(row, text=especialidad, width=150, text_color="gray").pack(side="left", padx=2)
        ctk.CTkLabel(row, text=cursos, width=200, anchor="w", text_color="silver").pack(side="left", padx=2)
        
        # Badge de estado
        color_estado = st.Colors.PUNTUAL if "Activo" in estado else st.Colors.FALTA
        ctk.CTkLabel(
            row,
            text=estado,
            width=80,
            fg_color=color_estado,
            corner_radius=5,
            text_color="white",
            font=("Arial", 9, "bold")
        ).pack(side="left", padx=2)
    
    def seleccionar_fila(self, row, dni):
        """Seleccionar fila y cargar datos en formulario"""
        messagebox.showinfo("Info", f"Seleccionado DNI: {dni}\n(Funcionalidad pendiente)")
    
    # =================== MÉTODOS DE LÓGICA ===================
    
    def guardar_docente(self):
        """Validar y guardar docente"""
        # Validaciones básicas
        dni = self.entry_dni.get().strip()
        nombres = self.entry_nombres.get().strip()
        ape_pat = self.entry_ape_pat.get().strip()
        
        if not dni or len(dni) != 8:
            messagebox.showwarning("Validación", "DNI debe tener 8 dígitos")
            return
        
        if not nombres or not ape_pat:
            messagebox.showwarning("Validación", "Complete campos obligatorios (*)")
            return
        
        # Obtener cursos seleccionados
        cursos_seleccionados = [
            curso for curso, var in self.checkbox_cursos.items() 
            if var.get()
        ]
        
        if not cursos_seleccionados:
            if not messagebox.askyesno("Confirmar", "No asignó cursos. ¿Continuar?"):
                return
        
        # Aquí llamarías al controller
        messagebox.showinfo(
            "Guardado",
            f"Docente: {nombres} {ape_pat}\nCursos: {', '.join(cursos_seleccionados)}\n\n✅ (Funcionalidad pendiente)"
        )
    
    def limpiar_formulario(self):
        """Limpiar todos los campos"""
        self.entry_dni.delete(0, 'end')
        self.entry_nombres.delete(0, 'end')
        self.entry_ape_pat.delete(0, 'end')
        self.entry_ape_mat.delete(0, 'end')
        self.entry_celular.delete(0, 'end')
        self.entry_email.delete(0, 'end')
        
        self.combo_especialidad.set("-- Seleccione --")
        self.combo_tipo_contrato.set("-- Seleccione --")
        self.combo_turno.set("-- Seleccione --")
        
        for var in self.checkbox_cursos.values():
            var.set(False)
        
        self.switch_activo.select()
    
    def buscar_docente(self, event):
        """Filtrar tabla por búsqueda"""
        criterio = self.entry_buscar.get().lower()
        messagebox.showinfo("Buscar", f"Buscando: '{criterio}'\n(Funcionalidad pendiente)")
    
    def filtrar_tabla(self):
        """Filtrar por estado (activos/inactivos/todos)"""
        filtro = self.radio_var.get()
        messagebox.showinfo("Filtro", f"Filtro: {filtro}\n(Funcionalidad pendiente)")
