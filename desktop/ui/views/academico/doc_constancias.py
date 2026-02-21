"""
ConstanciasView - Generación de constancias - VERSIÓN VISUAL PREMIUM (Musuq Cloud)
Refactor visual usando ThemeManager (TM), manteniendo la lógica original (mock).
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import date

import styles.tabla_style as st
from core.theme_manager import TM
from controllers.constancia_controller import ConstanciaController


class ConstanciasView(ctk.CTkFrame):
    def __init__(self, master, auth_client=None, **kwargs):
        super().__init__(master, fg_color="transparent")
        self.auth_client = auth_client

        self.controller = ConstanciaController()

        # Variables de estado
        self.alumno_seleccionado = None
        self.tipo_constancia_actual = None

        # Layout: 30% controles, 70% preview
        self.grid_columnconfigure(0, weight=3)  # Panel izquierdo
        self.grid_columnconfigure(1, weight=7)  # Panel derecho (preview)
        self.grid_rowconfigure(0, weight=1)

        # Paneles
        self._crear_panel_controles()
        self._crear_panel_preview()

    # ============================================================
    # PANEL IZQUIERDO: CONTROLES
    # ============================================================

    def _crear_panel_controles(self):
        self.panel_controles = ctk.CTkFrame(
            self,
            fg_color=TM.bg_panel(),
            corner_radius=15,
            border_width=1,
            border_color=TM.bg_card(),
        )
        self.panel_controles.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # --- HEADER ---
        ctk.CTkLabel(
            self.panel_controles,
            text="📄 CONSTANCIAS",
            font=("Roboto", 16, "bold"),
            text_color=TM.text(),
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            self.panel_controles,
            text="Generación de documentos oficiales",
            font=("Roboto", 10),
            text_color=TM.text_secondary(),
        ).pack(pady=(0, 15))

        # --- TIPO DE CONSTANCIA ---
        ctk.CTkLabel(
            self.panel_controles,
            text="Tipo de Documento",
            anchor="w",
            text_color=TM.text_secondary(),
            font=("Roboto", 11, "bold"),
        ).pack(fill="x", padx=20, pady=(10, 5))

        self.combo_tipo = ctk.CTkComboBox(
            self.panel_controles,
            values=[
                "Constancia de Matrícula",
                "Constancia de Estudios",
                "Constancia de Notas",
                "Constancia de Conducta",
                "Certificado de Estudios",
            ],
            command=self.cambiar_tipo_constancia,
            fg_color=TM.bg_card(),
            dropdown_fg_color=TM.bg_panel(),
            button_color=TM.primary(),
            button_hover_color=TM.hover(),
            text_color=TM.text(),
            state="readonly",
        )
        self.combo_tipo.set("Constancia de Matrícula")
        self.combo_tipo.pack(fill="x", padx=20, pady=(0, 15))

        # --- SEPARADOR ---
        ctk.CTkFrame(
            self.panel_controles, height=2, fg_color=TM.bg_card()
        ).pack(fill="x", padx=20, pady=10)

        # --- BUSCADOR DE ALUMNO ---
        ctk.CTkLabel(
            self.panel_controles,
            text="🔍 Buscar Estudiante",
            anchor="w",
            text_color=TM.text_secondary(),
            font=("Roboto", 11, "bold"),
        ).pack(fill="x", padx=20, pady=(10, 5))

        fr_search = ctk.CTkFrame(self.panel_controles, fg_color="transparent")
        fr_search.pack(fill="x", padx=20, pady=(0, 10))

        self.entry_buscar = ctk.CTkEntry(
            fr_search,
            placeholder_text="DNI o Nombre...",
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
            height=35,
        )
        self.entry_buscar.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry_buscar.bind("<KeyRelease>", self.buscar_alumno)

        self.btn_buscar = ctk.CTkButton(
            fr_search,
            text="🔎",
            width=40,
            fg_color=TM.bg_card(),
            hover_color=TM.hover(),
            command=self.buscar_alumno,
        )
        self.btn_buscar.pack(side="right")

        # --- RESULTADOS DE BÚSQUEDA ---
        ctk.CTkLabel(
            self.panel_controles,
            text="Resultados",
            anchor="w",
            text_color=TM.text_muted(),
            font=("Roboto", 9),
        ).pack(fill="x", padx=20, pady=(10, 2))

        self.scroll_resultados = ctk.CTkScrollableFrame(
            self.panel_controles,
            fg_color=TM.bg_card(),
            height=150,
        )
        self.scroll_resultados.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(
            self.scroll_resultados,
            text="... Escriba para buscar ...",
            text_color="gray",
        ).pack(pady=20)

        # --- SEPARADOR ---
        ctk.CTkFrame(
            self.panel_controles, height=2, fg_color=TM.bg_card()
        ).pack(fill="x", padx=20, pady=10)

        # --- OPCIONES ADICIONALES ---
        ctk.CTkLabel(
            self.panel_controles,
            text="⚙️ Opciones Adicionales",
            anchor="w",
            text_color=TM.text_secondary(),
            font=("Roboto", 11, "bold"),
        ).pack(fill="x", padx=20, pady=(10, 5))

        self.chk_incluir_notas = ctk.CTkCheckBox(
            self.panel_controles,
            text="Incluir Historial de Notas",
            fg_color=TM.primary(),
            hover_color=TM.hover(),
        )
        self.chk_incluir_notas.pack(anchor="w", padx=30, pady=2)

        self.chk_incluir_conducta = ctk.CTkCheckBox(
            self.panel_controles,
            text="Incluir Observaciones",
            fg_color=TM.primary(),
            hover_color=TM.hover(),
        )
        self.chk_incluir_conducta.pack(anchor="w", padx=30, pady=2)

        self.chk_con_foto = ctk.CTkCheckBox(
            self.panel_controles,
            text="Incluir Fotografía",
            fg_color=TM.primary(),
            hover_color=TM.hover(),
        )
        self.chk_con_foto.pack(anchor="w", padx=30, pady=2)

        # --- MOTIVO (OPCIONAL) ---
        ctk.CTkLabel(
            self.panel_controles,
            text="Motivo (opcional)",
            anchor="w",
            text_color=TM.text_muted(),
            font=("Roboto", 10),
        ).pack(fill="x", padx=20, pady=(15, 2))

        self.entry_motivo = ctk.CTkEntry(
            self.panel_controles,
            placeholder_text="Ej: Trámites personales",
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        self.entry_motivo.pack(fill="x", padx=20, pady=(0, 15))

        # --- BOTONES DE ACCIÓN ---
        self.btn_generar = ctk.CTkButton(
            self.panel_controles,
            text="🖨️ GENERAR PDF",
            height=45,
            font=("Roboto", 14, "bold"),
            fg_color=TM.success(),
            hover_color="#2ecc71",
            command=self.generar_constancia,
        )
        self.btn_generar.pack(fill="x", padx=20, pady=(10, 5))
        self.btn_generar.configure(state="disabled")

        self.btn_email = ctk.CTkButton(
            self.panel_controles,
            text="📧 Enviar por Email",
            height=35,
            fg_color=TM.primary(),
            hover_color=TM.hover(),
            command=self.enviar_email,
        )
        self.btn_email.pack(fill="x", padx=20, pady=5)
        self.btn_email.configure(state="disabled")

        # --- INFO FOOTER ---
        ctk.CTkLabel(
            self.panel_controles,
            text=(
                "💡 Tip: Los documentos se guardan"
                "automáticamente en /documentos/"
            ),
            text_color=TM.text_muted(),
            font=("Roboto", 9),
            justify="center",
        ).pack(side="bottom", pady=20)

    # ============================================================
    # PANEL DERECHO: PREVIEW
    # ============================================================

    def _crear_panel_preview(self):
        self.panel_preview = ctk.CTkFrame(
            self,
            fg_color=TM.bg_panel(),
            corner_radius=15,
            border_width=1,
            border_color=TM.bg_card(),
        )
        self.panel_preview.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")

        # --- HEADER PREVIEW ---
        fr_header = ctk.CTkFrame(self.panel_preview, fg_color="transparent")
        fr_header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            fr_header,
            text="VISTA PREVIA",
            text_color=TM.text_secondary(),
            font=("Roboto", 11),
        ).pack(side="left")

        self.lbl_fecha_preview = ctk.CTkLabel(
            fr_header,
            text=f"📅 {date.today().strftime('%d/%m/%Y')}",
            text_color=TM.text_secondary(),
            font=("Roboto", 10),
        )
        self.lbl_fecha_preview.pack(side="right")

        # --- CONTENEDOR DEL DOCUMENTO (Simulación A4) ---
        self.container_documento = ctk.CTkFrame(
            self.panel_preview,
            fg_color="transparent",
        )
        self.container_documento.pack(expand=True)

        # Sombra del documento
        self.shadow_frame = ctk.CTkFrame(
            self.container_documento,
            width=550,
            height=750,
            fg_color="#000000",
            corner_radius=5,
        )
        self.shadow_frame.place(x=5, y=5)

        # Documento (simulación A4)
        self.frame_documento = ctk.CTkFrame(
            self.container_documento,
            width=550,
            height=750,
            fg_color="white",
            corner_radius=5,
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
            fg_color=TM.bg_card(),
            hover_color=TM.hover(),
            command=self.actualizar_preview,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            fr_btns_bottom,
            text="📂 Abrir Carpeta",
            fg_color=TM.bg_card(),
            hover_color=TM.hover(),
            command=self.abrir_carpeta_documentos,
        ).pack(side="left", padx=5)

    # ============================================================
    # MÉTODOS DE RENDERIZADO (ADAPTADOS DEL ORIGINAL)
    # ============================================================

    def renderizar_plantilla_default(self):
        """Renderizar plantilla vacía"""
        for widget in self.frame_documento.winfo_children():
            widget.destroy()

        # Header con logo (simulado)
        fr_header_doc = ctk.CTkFrame(
            self.frame_documento,
            height=100,
            fg_color="#2c3e50",
            corner_radius=0,
        )
        fr_header_doc.pack(fill="x")

        ctk.CTkLabel(fr_header_doc, text="🏫", font=("Arial", 40)).pack(pady=10)

        ctk.CTkLabel(
            fr_header_doc,
            text="INSTITUCIÓN EDUCATIVA MUSUQ",
            font=("Arial", 14, "bold"),
            text_color="white",
        ).pack()

        # Contenido principal
        fr_contenido = ctk.CTkFrame(self.frame_documento, fg_color="white")
        fr_contenido.pack(fill="both", expand=True, padx=40, pady=30)

        ctk.CTkLabel(
            fr_contenido,
            text="CONSTANCIA DE MATRÍCULA",
            font=("Arial", 18, "bold", "underline"),
            text_color="black",
        ).pack(pady=(20, 30))

        texto_plantilla = (
            "La Dirección de la INSTITUCIÓN EDUCATIVA MUSUQ,"
            "CERTIFICA:"
            "Que el/la estudiante:"
            "[NOMBRE COMPLETO DEL ALUMNO]"
            "DNI: [NÚMERO DE DNI]"
            "Código de Matrícula: [CÓDIGO]"
            "Se encuentra MATRICULADO(A) en el presente año académico 2026"
            "en la modalidad [MODALIDAD] - Grupo [GRUPO]"
            "en la carrera de [CARRERA]."
            "Se expide la presente constancia a solicitud del interesado"
            "para los fines que estime conveniente."
        )

        ctk.CTkLabel(
            fr_contenido,
            text=texto_plantilla,
            font=("Arial", 11),
            text_color="#2c3e50",
            justify="left",
            anchor="w",
        ).pack(fill="both", expand=True)

        # Footer con fecha y firma
        fr_footer = ctk.CTkFrame(fr_contenido, fg_color="white")
        fr_footer.pack(side="bottom", pady=(20, 0))

        ctk.CTkLabel(
            fr_footer,
            text=f"Lima, {date.today().strftime('%d de %B de %Y')}",
            font=("Arial", 10),
            text_color="black",
        ).pack()

        ctk.CTkFrame(fr_footer, width=200, height=2, fg_color="black").pack(
            pady=(40, 5)
        )

        ctk.CTkLabel(
            fr_footer,
            text="Firma y Sello de la Dirección",
            font=("Arial", 9),
            text_color="gray",
        ).pack()

    def renderizar_con_datos(self, alumno):
        """Renderizar plantilla con datos del alumno"""
        for widget in self.frame_documento.winfo_children():
            widget.destroy()

        fr_header_doc = ctk.CTkFrame(
            self.frame_documento,
            height=100,
            fg_color="#2c3e50",
            corner_radius=0,
        )
        fr_header_doc.pack(fill="x")

        ctk.CTkLabel(fr_header_doc, text="🏫", font=("Arial", 40)).pack(pady=10)

        ctk.CTkLabel(
            fr_header_doc,
            text="INSTITUCIÓN EDUCATIVA MUSUQ",
            font=("Arial", 14, "bold"),
            text_color="white",
        ).pack()

        fr_contenido = ctk.CTkFrame(self.frame_documento, fg_color="white")
        fr_contenido.pack(fill="both", expand=True, padx=40, pady=30)

        tipo = self.combo_tipo.get()

        ctk.CTkLabel(
            fr_contenido,
            text=tipo.upper(),
            font=("Arial", 18, "bold", "underline"),
            text_color="black",
        ).pack(pady=(20, 30))

        nombre_completo = alumno.nombre_completo

        if "Matrícula" in tipo:
            texto = f"""
La Dirección de la INSTITUCIÓN EDUCATIVA MUSUQ,

CERTIFICA:

Que el/la estudiante:

{nombre_completo}

DNI: {alumno.dni}

Código de Matrícula: {alumno.codigo_matricula}

Se encuentra MATRICULADO(A) en el presente año académico {date.today().year}

en la modalidad {alumno.modalidad} - Grupo {alumno.grupo}

en la carrera de {alumno.carrera}.

Se expide la presente constancia a solicitud del interesado

para los fines que estime conveniente.
"""
        elif "Estudios" in tipo:
            texto = f"""
La Dirección de la INSTITUCIÓN EDUCATIVA MUSUQ,

CERTIFICA:

Que {nombre_completo}, identificado(a) con DNI {alumno.dni},

es estudiante REGULAR de esta institución con código {alumno.codigo_matricula}.

Actualmente cursa estudios en la carrera de {alumno.carrera},

modalidad {alumno.modalidad}, horario {alumno.horario}.

Se expide el presente documento para los fines que considere conveniente.
"""
        else:
            texto = f"""
La Dirección de la INSTITUCIÓN EDUCATIVA MUSUQ,

CERTIFICA:

Que {nombre_completo}

DNI: {alumno.dni}

Código: {alumno.codigo_matricula}

[Contenido específico del documento]
"""

        ctk.CTkLabel(
            fr_contenido,
            text=texto,
            font=("Arial", 11),
            text_color="#2c3e50",
            justify="left",
        ).pack(fill="both", expand=True)

        fr_footer = ctk.CTkFrame(fr_contenido, fg_color="white")
        fr_footer.pack(side="bottom", pady=(20, 0))

        ctk.CTkLabel(
            fr_footer,
            text=f"Lima, {date.today().strftime('%d de %B de %Y')}",
            font=("Arial", 10),
            text_color="black",
        ).pack()

        ctk.CTkFrame(fr_footer, width=200, height=2, fg_color="black").pack(
            pady=(40, 5)
        )

        ctk.CTkLabel(
            fr_footer,
            text="Firma y Sello de la Dirección",
            font=("Arial", 9),
            text_color="gray",
        ).pack()

    # ============================================================
    # LÓGICA (IGUAL QUE EL ORIGINAL, ESTILO MUSUQ)
    # ============================================================

    def cambiar_tipo_constancia(self, valor):
        self.tipo_constancia_actual = valor
        if self.alumno_seleccionado:
            self.renderizar_con_datos(self.alumno_seleccionado)

    def buscar_alumno(self, event=None):
        criterio = self.entry_buscar.get().strip()

        for widget in self.scroll_resultados.winfo_children():
            widget.destroy()

        if not criterio:
            ctk.CTkLabel(
                self.scroll_resultados,
                text="... Escriba para buscar ...",
                text_color="gray",
            ).pack(pady=20)
            return

        # Buscar usando controller
        resultados = self.controller.buscar_alumnos(criterio)

        if not resultados:
            ctk.CTkLabel(
                self.scroll_resultados,
                text="Sin resultados",
                text_color="gray",
            ).pack(pady=20)
        else:
            for alumno in resultados:
                btn = ctk.CTkButton(
                    self.scroll_resultados,
                    text=f"[{alumno.codigo_matricula}] {alumno.apellidos}, {alumno.nombres}",
                    fg_color="transparent",
                    hover_color=TM.bg_card(),
                    anchor="w",
                    height=35,
                    command=lambda a=alumno: self.seleccionar_alumno(a),
                )
                btn.pack(fill="x", pady=1)

    def seleccionar_alumno(self, alumno):
        self.alumno_seleccionado = alumno
        self.btn_generar.configure(state="normal")
        self.btn_email.configure(state="normal")

        self.entry_buscar.delete(0, "end")
        self.entry_buscar.insert(0, f"{alumno.codigo_matricula} - {alumno.apellidos}")

        self.renderizar_con_datos(alumno)

        for widget in self.scroll_resultados.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.scroll_resultados,
            text=f"✅ Seleccionado: {alumno.apellidos}, {alumno.nombres}",
            text_color=st.Colors.PUNTUAL,
            font=("Roboto", 11, "bold"),
        ).pack(pady=20)

    def generar_constancia(self):
        if not self.alumno_seleccionado:
            messagebox.showwarning(
                "Advertencia", "Debe seleccionar un alumno primero"
            )
            return

        tipo = self.combo_tipo.get()
        alumno = self.alumno_seleccionado

        opciones = {
            "incluir_notas": self.chk_incluir_notas.get(),
            "incluir_conducta": self.chk_incluir_conducta.get(),
            "incluir_foto": self.chk_con_foto.get(),
            "motivo": self.entry_motivo.get()
        }

        exito, msg = self.controller.generar_constancia_pdf(tipo, alumno, opciones)
        
        if exito:
            messagebox.showinfo("Éxito", msg)
        else:
            messagebox.showerror("Error", msg)

    def enviar_email(self):
        messagebox.showinfo(
            "Email",
            "Funcionalidad de envío por email (Pendiente de implementar)",
        )

    def actualizar_preview(self):
        if self.alumno_seleccionado:
            self.renderizar_con_datos(self.alumno_seleccionado)
        else:
            self.renderizar_plantilla_default()

    def abrir_carpeta_documentos(self):
        messagebox.showinfo(
            "Carpeta",
            "Abrir carpeta: /documentos/constancias/ (Funcionalidad pendiente)",
        )
