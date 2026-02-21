# app/ui/doc_constancias_view.py
import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import date
import app.styles.tabla_style as st

class ConstanciasView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        # self.controller = ConstanciaController()  # ← Después
        
        # Variables de estado 
        self.alumno_seleccionado = None
        self.tipo_constancia_actual = None
        
        self.configure(fg_color=st.Colors.BG_MAIN)
        
        # Layout: 30% controles, 70% preview
        self.grid_columnconfigure(0, weight=3)  # Panel izquierdo
        self.grid_columnconfigure(1, weight=7)  # Panel derecho (preview)
        self.grid_rowconfigure(0, weight=1)
        
        # ============================
        # PANEL IZQUIERDO: CONTROLES
        # ============================
        self.panel_controles = ctk.CTkFrame(
            self,
            fg_color="#2d2d2d",
            corner_radius=15,
            border_width=1,
            border_color="#3d3d3d"
        )
        self.panel_controles.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # --- HEADER ---
        ctk.CTkLabel(
            self.panel_controles,
            text="📄 CONSTANCIAS",
            font=("Roboto", 16, "bold"),
            text_color="#ecf0f1"
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(
            self.panel_controles,
            text="Generación de documentos oficiales",
            font=("Roboto", 10),
            text_color="gray"
        ).pack(pady=(0, 20))
        
        # --- TIPO DE CONSTANCIA ---
        ctk.CTkLabel(
            self.panel_controles,
            text="Tipo de Documento",
            anchor="w",
            text_color="#bdc3c7",
            font=("Roboto", 11, "bold")
        ).pack(fill="x", padx=20, pady=(10, 5))
        
        self.combo_tipo = ctk.CTkComboBox(
            self.panel_controles,
            values=[
                "Constancia de Matrícula",
                "Constancia de Estudios",
                "Constancia de Notas",
                "Constancia de Conducta",
                "Certificado de Estudios"
            ],
            command=self.cambiar_tipo_constancia,
            fg_color="#34495e",
            dropdown_fg_color="#2d2d2d",
            button_color="#3498db",
            button_hover_color="#2980b9",
            state="readonly"
        )
        self.combo_tipo.set("Constancia de Matrícula")
        self.combo_tipo.pack(fill="x", padx=20, pady=(0, 15))
        
        # --- SEPARADOR ---
        ctk.CTkFrame(self.panel_controles, height=2, fg_color="#404040").pack(fill="x", padx=20, pady=10)
        
        # --- BUSCADOR DE ALUMNO ---
        ctk.CTkLabel(
            self.panel_controles,
            text="🔍 Buscar Estudiante",
            anchor="w",
            text_color="#bdc3c7",
            font=("Roboto", 11, "bold")
        ).pack(fill="x", padx=20, pady=(10, 5))
        
        fr_search = ctk.CTkFrame(self.panel_controles, fg_color="transparent")
        fr_search.pack(fill="x", padx=20, pady=(0, 10))
        
        self.entry_buscar = ctk.CTkEntry(
            fr_search,
            placeholder_text="DNI o Nombre...",
            fg_color="#1a1a1a",
            border_color="#34495e",
            height=35
        )
        self.entry_buscar.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry_buscar.bind("<KeyRelease>", self.buscar_alumno)
        
        self.btn_buscar = ctk.CTkButton(
            fr_search,
            text="🔎",
            width=40,
            fg_color="#34495e",
            hover_color="#2c3e50",
            command=self.buscar_alumno
        )
        self.btn_buscar.pack(side="right")
        
        # --- RESULTADOS DE BÚSQUEDA ---
        ctk.CTkLabel(
            self.panel_controles,
            text="Resultados",
            anchor="w",
            text_color="gray",
            font=("Roboto", 9)
        ).pack(fill="x", padx=20, pady=(10, 2))
        
        self.scroll_resultados = ctk.CTkScrollableFrame(
            self.panel_controles,
            fg_color="#2b2b2b",
            height=150
        )
        self.scroll_resultados.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            self.scroll_resultados,
            text="... Escriba para buscar ...",
            text_color="gray"
        ).pack(pady=20)
        
        # --- SEPARADOR ---
        ctk.CTkFrame(self.panel_controles, height=2, fg_color="#404040").pack(fill="x", padx=20, pady=10)
        
        # --- OPCIONES ADICIONALES ---
        ctk.CTkLabel(
            self.panel_controles,
            text="⚙️ Opciones Adicionales",
            anchor="w",
            text_color="#bdc3c7",
            font=("Roboto", 11, "bold")
        ).pack(fill="x", padx=20, pady=(10, 5))
        
        self.chk_incluir_notas = ctk.CTkCheckBox(
            self.panel_controles,
            text="Incluir Historial de Notas",
            fg_color="#3498db",
            hover_color="#2980b9"
        )
        self.chk_incluir_notas.pack(anchor="w", padx=30, pady=2)
        
        self.chk_incluir_conducta = ctk.CTkCheckBox(
            self.panel_controles,
            text="Incluir Observaciones",
            fg_color="#3498db",
            hover_color="#2980b9"
        )
        self.chk_incluir_conducta.pack(anchor="w", padx=30, pady=2)
        
        self.chk_con_foto = ctk.CTkCheckBox(
            self.panel_controles,
            text="Incluir Fotografía",
            fg_color="#3498db",
            hover_color="#2980b9"
        )
        self.chk_con_foto.pack(anchor="w", padx=30, pady=2)
        
        # --- MOTIVO (OPCIONAL) ---
        ctk.CTkLabel(
            self.panel_controles,
            text="Motivo (opcional)",
            anchor="w",
            text_color="gray",
            font=("Roboto", 10)
        ).pack(fill="x", padx=20, pady=(15, 2))
        
        self.entry_motivo = ctk.CTkEntry(
            self.panel_controles,
            placeholder_text="Ej: Trámites personales",
            fg_color="#1a1a1a",
            border_color="#34495e"
        )
        self.entry_motivo.pack(fill="x", padx=20, pady=(0, 15))
        
        # --- BOTONES DE ACCIÓN ---
        self.btn_generar = ctk.CTkButton(
            self.panel_controles,
            text="🖨️ GENERAR PDF",
            height=45,
            font=("Roboto", 14, "bold"),
            fg_color="#27ae60",
            hover_color="#2ecc71",
            command=self.generar_constancia
        )
        self.btn_generar.pack(fill="x", padx=20, pady=(10, 5))
        self.btn_generar.configure(state="disabled")  # Activar al seleccionar alumno
        
        self.btn_email = ctk.CTkButton(
            self.panel_controles,
            text="📧 Enviar por Email",
            height=35,
            fg_color="#3498db",
            hover_color="#2980b9",
            command=self.enviar_email
        )
        self.btn_email.pack(fill="x", padx=20, pady=5)
        self.btn_email.configure(state="disabled")
        
        # --- INFO FOOTER ---
        ctk.CTkLabel(
            self.panel_controles,
            text="💡 Tip: Los documentos se guardan\nautomáticamente en /documentos/",
            text_color="#7f8c8d",
            font=("Roboto", 9),
            justify="center"
        ).pack(side="bottom", pady=20)
        
        # ============================
        # PANEL DERECHO: PREVIEW
        # ============================
        self.panel_preview = ctk.CTkFrame(
            self,
            fg_color="#121212",
            corner_radius=15,
            border_width=1,
            border_color="#3d3d3d"
        )
        self.panel_preview.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        
        # --- HEADER PREVIEW ---
        fr_header = ctk.CTkFrame(self.panel_preview, fg_color="transparent")
        fr_header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            fr_header,
            text="VISTA PREVIA",
            text_color="#7f8c8d",
            font=("Roboto", 11)
        ).pack(side="left")
        
        self.lbl_fecha_preview = ctk.CTkLabel(
            fr_header,
            text=f"📅 {date.today().strftime('%d/%m/%Y')}",
            text_color="#95a5a6",
            font=("Roboto", 10)
        )
        self.lbl_fecha_preview.pack(side="right")
        
        # --- CONTENEDOR DEL DOCUMENTO (Simulación A4) ---
        self.container_documento = ctk.CTkFrame(self.panel_preview, fg_color="transparent")
        self.container_documento.pack(expand=True)
        
        # Sombra del documento
        self.shadow_frame = ctk.CTkFrame(
            self.container_documento,
            width=550,
            height=750,
            fg_color="#000000",
            corner_radius=5
        )
        self.shadow_frame.place(x=5, y=5)
        
        # Documento (simulación A4)
        self.frame_documento = ctk.CTkFrame(
            self.container_documento,
            width=550,
            height=750,
            fg_color="white",
            corner_radius=5
        )
        self.frame_documento.place(x=0, y=0)
        
        # Forzar tamaño
        self.container_documento.configure(width=560, height=760)
        
        # Renderizar plantilla por defecto
        self.renderizar_plantilla_default()
        
        # --- BOTONES INFERIORES ---
        fr_btns_bottom = ctk.CTkFrame(self.panel_preview, fg_color="transparent")
        fr_btns_bottom.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkButton(
            fr_btns_bottom,
            text="🔄 Actualizar Vista",
            fg_color="#404040",
            hover_color="#505050",
            command=self.actualizar_preview
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            fr_btns_bottom,
            text="📂 Abrir Carpeta",
            fg_color="#404040",
            hover_color="#505050",
            command=self.abrir_carpeta_documentos
        ).pack(side="left", padx=5)
    
    # =================== MÉTODOS DE RENDERIZADO ===================
    
    def renderizar_plantilla_default(self):
        """Renderizar plantilla vacía"""
        # Limpiar
        for widget in self.frame_documento.winfo_children():
            widget.destroy()
        
        # Header con logo (simulado)
        fr_header_doc = ctk.CTkFrame(
            self.frame_documento,
            height=100,
            fg_color="#2c3e50",
            corner_radius=0
        )
        fr_header_doc.pack(fill="x")
        
        ctk.CTkLabel(
            fr_header_doc,
            text="🏫",
            font=("Arial", 40)
        ).pack(pady=10)
        
        ctk.CTkLabel(
            fr_header_doc,
            text="INSTITUCIÓN EDUCATIVA MUSUQ",
            font=("Arial", 14, "bold"),
            text_color="white"
        ).pack()
        
        # Contenido principal
        fr_contenido = ctk.CTkFrame(self.frame_documento, fg_color="white")
        fr_contenido.pack(fill="both", expand=True, padx=40, pady=30)
        
        # Título
        ctk.CTkLabel(
            fr_contenido,
            text="CONSTANCIA DE MATRÍCULA",
            font=("Arial", 18, "bold", "underline"),
            text_color="black"
        ).pack(pady=(20, 30))
        
        # Cuerpo
        texto_plantilla = """
        La Dirección de la INSTITUCIÓN EDUCATIVA MUSUQ,
        
        CERTIFICA:
        
        Que el/la estudiante:
        
        [NOMBRE COMPLETO DEL ALUMNO]
        DNI: [NÚMERO DE DNI]
        Código de Matrícula: [CÓDIGO]
        
        Se encuentra MATRICULADO(A) en el presente año académico 2026
        en la modalidad [MODALIDAD] - Grupo [GRUPO]
        en la carrera de [CARRERA].
        
        Se expide la presente constancia a solicitud del interesado
        para los fines que estime conveniente.
        """
        
        ctk.CTkLabel(
            fr_contenido,
            text=texto_plantilla,
            font=("Arial", 11),
            text_color="#2c3e50",
            justify="left",
            anchor="w"
        ).pack(fill="both", expand=True)
        
        # Footer con fecha y firma
        fr_footer = ctk.CTkFrame(fr_contenido, fg_color="white")
        fr_footer.pack(side="bottom", pady=(20, 0))
        
        ctk.CTkLabel(
            fr_footer,
            text=f"Lima, {date.today().strftime('%d de %B de %Y')}",
            font=("Arial", 10),
            text_color="black"
        ).pack()
        
        ctk.CTkFrame(fr_footer, width=200, height=2, fg_color="black").pack(pady=(40, 5))
        
        ctk.CTkLabel(
            fr_footer,
            text="Firma y Sello de la Dirección",
            font=("Arial", 9),
            text_color="gray"
        ).pack()
    
    def renderizar_con_datos(self, alumno):
        """Renderizar plantilla con datos del alumno"""
        # Limpiar
        for widget in self.frame_documento.winfo_children():
            widget.destroy()
        
        # Header (igual que antes)
        fr_header_doc = ctk.CTkFrame(
            self.frame_documento,
            height=100,
            fg_color="#2c3e50",
            corner_radius=0
        )
        fr_header_doc.pack(fill="x")
        
        ctk.CTkLabel(fr_header_doc, text="🏫", font=("Arial", 40)).pack(pady=10)
        ctk.CTkLabel(
            fr_header_doc,
            text="INSTITUCIÓN EDUCATIVA MUSUQ",
            font=("Arial", 14, "bold"),
            text_color="white"
        ).pack()
        
        # Contenido con datos reales
        fr_contenido = ctk.CTkFrame(self.frame_documento, fg_color="white")
        fr_contenido.pack(fill="both", expand=True, padx=40, pady=30)
        
        tipo = self.combo_tipo.get()
        ctk.CTkLabel(
            fr_contenido,
            text=tipo.upper(),
            font=("Arial", 18, "bold", "underline"),
            text_color="black"
        ).pack(pady=(20, 30))
        
        # Texto dinámico según tipo
        nombre_completo = f"{alumno['apellidos']}, {alumno['nombres']}"
        
        if "Matrícula" in tipo:
            texto = f"""
        La Dirección de la INSTITUCIÓN EDUCATIVA MUSUQ,
        
        CERTIFICA:
        
        Que el/la estudiante:
        
        {nombre_completo}
        DNI: {alumno['dni']}
        Código de Matrícula: {alumno['codigo']}
        
        Se encuentra MATRICULADO(A) en el presente año académico 2026
        en la modalidad {alumno['modalidad']} - Grupo {alumno['grupo']}
        en la carrera de {alumno['carrera']}.
        
        Se expide la presente constancia a solicitud del interesado
        para los fines que estime conveniente.
            """
        elif "Estudios" in tipo:
            texto = f"""
        La Dirección de la INSTITUCIÓN EDUCATIVA MUSUQ,
        
        CERTIFICA:
        
        Que {nombre_completo}, identificado(a) con DNI {alumno['dni']},
        es estudiante REGULAR de esta institución con código {alumno['codigo']}.
        
        Actualmente cursa estudios en la carrera de {alumno['carrera']},
        modalidad {alumno['modalidad']}, horario {alumno['horario']}.
        
        Se expide el presente documento para los fines que considere conveniente.
            """
        else:
            texto = f"""
        La Dirección de la INSTITUCIÓN EDUCATIVA MUSUQ,
        
        CERTIFICA:
        
        Que {nombre_completo}
        DNI: {alumno['dni']}
        Código: {alumno['codigo']}
        
        [Contenido específico del documento]
            """
        
        ctk.CTkLabel(
            fr_contenido,
            text=texto,
            font=("Arial", 11),
            text_color="#2c3e50",
            justify="left"
        ).pack(fill="both", expand=True)
        
        # Footer
        fr_footer = ctk.CTkFrame(fr_contenido, fg_color="white")
        fr_footer.pack(side="bottom", pady=(20, 0))
        
        ctk.CTkLabel(
            fr_footer,
            text=f"Lima, {date.today().strftime('%d de %B de %Y')}",
            font=("Arial", 10),
            text_color="black"
        ).pack()
        
        ctk.CTkFrame(fr_footer, width=200, height=2, fg_color="black").pack(pady=(40, 5))
        ctk.CTkLabel(
            fr_footer,
            text="Firma y Sello de la Dirección",
            font=("Arial", 9),
            text_color="gray"
        ).pack()
    
    # =================== MÉTODOS DE LÓGICA ===================
    
    def cambiar_tipo_constancia(self, valor):
        """Cambiar tipo de constancia"""
        self.tipo_constancia_actual = valor
        if self.alumno_seleccionado:
            self.renderizar_con_datos(self.alumno_seleccionado)
    
    def buscar_alumno(self, event=None):
        """Buscar alumnos por criterio"""
        criterio = self.entry_buscar.get().strip()
        
        # Limpiar resultados
        for widget in self.scroll_resultados.winfo_children():
            widget.destroy()
        
        if not criterio:
            ctk.CTkLabel(
                self.scroll_resultados,
                text="... Escriba para buscar ...",
                text_color="gray"
            ).pack(pady=20)
            return
        
        # Simulación de búsqueda (reemplazar con controller)
        resultados_dummy = [
            {"dni": "43210987", "nombres": "Juan Carlos", "apellidos": "PÉREZ GÓMEZ", 
             "codigo": "POA250001", "grupo": "A", "carrera": "Medicina", "modalidad": "Primera Opción", "horario": "Mañana"},
            {"dni": "41234567", "nombres": "María Elena", "apellidos": "LÓPEZ RAMÍREZ",
             "codigo": "POA250045", "grupo": "B", "carrera": "Ingeniería", "modalidad": "Ordinario", "horario": "Tarde"},
        ]
        
        # Filtrar resultados (simulado)
        filtrados = [a for a in resultados_dummy if criterio.lower() in a['nombres'].lower() 
                     or criterio in a['dni'] or criterio.lower() in a['apellidos'].lower()]
        
        if not filtrados:
            ctk.CTkLabel(
                self.scroll_resultados,
                text="Sin resultados",
                text_color="gray"
            ).pack(pady=20)
        else:
            for alumno in filtrados:
                btn = ctk.CTkButton(
                    self.scroll_resultados,
                    text=f"[{alumno['codigo']}] {alumno['apellidos']}, {alumno['nombres']}",
                    fg_color="transparent",
                    hover_color="#404040",
                    anchor="w",
                    height=35,
                    command=lambda a=alumno: self.seleccionar_alumno(a)
                )
                btn.pack(fill="x", pady=1)
    
    def seleccionar_alumno(self, alumno):
        """Seleccionar alumno y actualizar preview"""
        self.alumno_seleccionado = alumno
        self.btn_generar.configure(state="normal")
        self.btn_email.configure(state="normal")
        
        # Limpiar búsqueda
        self.entry_buscar.delete(0, 'end')
        self.entry_buscar.insert(0, f"{alumno['codigo']} - {alumno['apellidos']}")
        
        # Actualizar preview
        self.renderizar_con_datos(alumno)
        
        # Mostrar confirmación visual
        for widget in self.scroll_resultados.winfo_children():
            widget.destroy()
        ctk.CTkLabel(
            self.scroll_resultados,
            text=f"✅ Seleccionado:\n{alumno['apellidos']}, {alumno['nombres']}",
            text_color=st.Colors.PUNTUAL,
            font=("Roboto", 11, "bold")
        ).pack(pady=20)
    
    def generar_constancia(self):
        """Generar PDF de la constancia"""
        if not self.alumno_seleccionado:
            messagebox.showwarning("Advertencia", "Debe seleccionar un alumno primero")
            return
        
        # Aquí llamarías al controller para generar PDF
        tipo = self.combo_tipo.get()
        alumno = self.alumno_seleccionado
        
        messagebox.showinfo(
            "Generado",
            f"Constancia generada:\n\n"
            f"Tipo: {tipo}\n"
            f"Alumno: {alumno['apellidos']}, {alumno['nombres']}\n"
            f"Archivo: constancia_{alumno['codigo']}_{date.today().strftime('%Y%m%d')}.pdf\n\n"
            f"✅ (Funcionalidad pendiente)"
        )
    
    def enviar_email(self):
        """Enviar constancia por email"""
        messagebox.showinfo("Email", "Funcionalidad de envío por email\n(Pendiente de implementar)")
    
    def actualizar_preview(self):
        """Refrescar vista previa"""
        if self.alumno_seleccionado:
            self.renderizar_con_datos(self.alumno_seleccionado)
        else:
            self.renderizar_plantilla_default()
    
    def abrir_carpeta_documentos(self):
        """Abrir carpeta donde se guardan los documentos"""
        messagebox.showinfo("Carpeta", "Abrir carpeta: /documentos/constancias/\n(Funcionalidad pendiente)")
