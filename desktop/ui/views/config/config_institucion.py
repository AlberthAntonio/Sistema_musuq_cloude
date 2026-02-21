"""
ConfigInstitucionView - VERSIÓN VISUAL PREMIUM (Musuq Cloud)
Refactor visual usando ThemeManager (TM).
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import os

import styles.tabla_style as st
from core.theme_manager import TM


class ConfigInstitucionView(ctk.CTkFrame):
    def __init__(self, master, auth_client=None):
        super().__init__(master, fg_color=TM.bg_main())

        # self.controller = ConfigController() # ← Después

        self.logo_path = None
        self.logo_image = None

        # Layout principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Contenedor central con scroll
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Header
        self._crear_header()

        # Tabview (pestañas)
        self._crear_tabview()

        # Cargar valores actuales
        self.cargar_configuracion()

    def _crear_header(self):
        """Header con título"""
        fr_header = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        fr_header.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            fr_header,
            text="⚙️ CONFIGURACIÓN",
            font=("Roboto", 20, "bold"),
            text_color=TM.text(),
        ).pack(side="left")

        ctk.CTkLabel(
            fr_header,
            text="Datos de la institución",
            font=("Roboto", 11),
            text_color=TM.text_secondary(),
        ).pack(side="left", padx=(20, 0))

    def _crear_tabview(self):
        """Tabview con pestañas"""
        self.tabview = ctk.CTkTabview(
            self.scroll_container,
            fg_color=TM.bg_panel(),
            segmented_button_fg_color=TM.bg_card(),
            segmented_button_selected_color=TM.primary(),
            segmented_button_selected_hover_color=TM.hover(),
        )
        self.tabview.pack(fill="both", expand=True)

        # Crear pestañas
        self.tabview.add("📄 Datos Generales")
        self.tabview.add("📚 Configuración Académica")
        self.tabview.add("🔢 Códigos de Matrícula")
        self.tabview.add("🎨 Apariencia")

        # Construir contenido
        self._crear_tab_datos_generales()
        self._crear_tab_academica()
        self._crear_tab_codigos()
        self._crear_tab_apariencia()

        # Botones finales
        self._crear_botones_finales()

    def _crear_tab_datos_generales(self):
        """PESTAÑA 1: DATOS GENERALES"""
        tab1 = self.tabview.tab("📄 Datos Generales")
        fr_datos = ctk.CTkFrame(tab1, fg_color="transparent")
        fr_datos.pack(fill="both", expand=True, padx=30, pady=20)

        # Nombre completo
        self.entry_nombre = self.campo(
            fr_datos, "Nombre Completo *", "INSTITUCIÓN EDUCATIVA MUSUQ"
        )

        # Nombre corto
        self.entry_nombre_corto = self.campo(
            fr_datos, "Nombre Corto (para carnets) *", "I.E. MUSUQ"
        )

        # RUC y Director (fila doble)
        fr_row1 = ctk.CTkFrame(fr_datos, fg_color="transparent")
        fr_row1.pack(fill="x", pady=5)

        fr_ruc = ctk.CTkFrame(fr_row1, fg_color="transparent")
        fr_ruc.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkLabel(
            fr_ruc, text="RUC", anchor="w", text_color=TM.text_secondary()
        ).pack(fill="x")

        self.entry_ruc = ctk.CTkEntry(
            fr_ruc,
            placeholder_text="20123456789",
            height=40,
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        self.entry_ruc.pack(fill="x")

        fr_director = ctk.CTkFrame(fr_row1, fg_color="transparent")
        fr_director.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            fr_director, text="Director(a)", anchor="w", text_color=TM.text_secondary()
        ).pack(fill="x")

        self.entry_director = ctk.CTkEntry(
            fr_director,
            placeholder_text="Nombres completos del director",
            height=40,
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        self.entry_director.pack(fill="x")

        # Dirección
        self.entry_direccion = self.campo(
            fr_datos, "Dirección", "Av. Principal 123, San Juan de Lurigancho, Lima"
        )

        # Teléfono y Email (fila doble)
        fr_row2 = ctk.CTkFrame(fr_datos, fg_color="transparent")
        fr_row2.pack(fill="x", pady=5)

        fr_tel = ctk.CTkFrame(fr_row2, fg_color="transparent")
        fr_tel.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkLabel(
            fr_tel, text="Teléfono", anchor="w", text_color=TM.text_secondary()
        ).pack(fill="x")

        self.entry_telefono = ctk.CTkEntry(
            fr_tel,
            placeholder_text="(01) 123-4567",
            height=40,
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        self.entry_telefono.pack(fill="x")

        fr_email = ctk.CTkFrame(fr_row2, fg_color="transparent")
        fr_email.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            fr_email, text="Email", anchor="w", text_color=TM.text_secondary()
        ).pack(fill="x")

        self.entry_email = ctk.CTkEntry(
            fr_email,
            placeholder_text="contacto@institucion.edu.pe",
            height=40,
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        self.entry_email.pack(fill="x")

        # Separador
        ctk.CTkFrame(fr_datos, height=2, fg_color=TM.bg_card()).pack(fill="x", pady=20)

        # Logo
        ctk.CTkLabel(
            fr_datos,
            text="🏢 LOGO INSTITUCIONAL",
            font=("Roboto", 14, "bold"),
            text_color=TM.primary(),
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        fr_logo = ctk.CTkFrame(fr_datos, fg_color=TM.bg_main(), corner_radius=10)
        fr_logo.pack(fill="x", pady=10)

        # Contenedor de preview
        self.fr_logo_preview = ctk.CTkFrame(
            fr_logo, width=150, height=150, fg_color=TM.bg_card(), corner_radius=10
        )
        self.fr_logo_preview.pack(side="left", padx=20, pady=20)
        self.fr_logo_preview.pack_propagate(False)

        # Placeholder de logo
        self.lbl_logo = ctk.CTkLabel(
            self.fr_logo_preview,
            text="🏫\nSin Logo",
            text_color=TM.text_muted(),
            font=("Arial", 12),
        )
        self.lbl_logo.place(relx=0.5, rely=0.5, anchor="center")

        # Botones de logo
        fr_btns_logo = ctk.CTkFrame(fr_logo, fg_color="transparent")
        fr_btns_logo.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            fr_btns_logo,
            text="Formatos aceptados: PNG, JPG (máx. 2MB)\nRecomendado: 500x500 px, fondo transparente",
            text_color=TM.text_secondary(),
            font=("Roboto", 9),
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        self.btn_cargar_logo = ctk.CTkButton(
            fr_btns_logo,
            text="📂 Cargar Logo",
            fg_color=TM.primary(),
            hover_color=TM.hover(),
            command=self.cargar_logo,
        )
        self.btn_cargar_logo.pack(fill="x", pady=5)

        self.btn_eliminar_logo = ctk.CTkButton(
            fr_btns_logo,
            text="🗑️ Eliminar Logo",
            fg_color=TM.danger(),
            hover_color="#e74c3c",
            command=self.eliminar_logo,
            state="disabled",
        )
        self.btn_eliminar_logo.pack(fill="x", pady=5)

    def _crear_tab_academica(self):
        """PESTAÑA 2: CONFIGURACIÓN ACADÉMICA"""
        tab2 = self.tabview.tab("📚 Configuración Académica")
        fr_academico = ctk.CTkFrame(tab2, fg_color="transparent")
        fr_academico.pack(fill="both", expand=True, padx=30, pady=20)

        # Horarios de entrada
        ctk.CTkLabel(
            fr_academico,
            text="⏰ HORARIOS DE INGRESO",
            font=("Roboto", 14, "bold"),
            text_color=TM.primary(),
            anchor="w",
        ).pack(fill="x", pady=(0, 15))

        # Turno mañana
        fr_manana = ctk.CTkFrame(fr_academico, fg_color=TM.bg_card(), corner_radius=10)
        fr_manana.pack(fill="x", pady=5)

        ctk.CTkLabel(
            fr_manana,
            text="🌅 Turno Mañana",
            font=("Roboto", 12, "bold"),
            text_color=TM.text(),
        ).pack(side="left", padx=20, pady=15)

        ctk.CTkLabel(
            fr_manana, text="Hora de entrada:", text_color=TM.text_secondary()
        ).pack(side="left", padx=(50, 5))

        self.entry_hora_manana = ctk.CTkEntry(
            fr_manana,
            width=80,
            placeholder_text="08:00",
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        self.entry_hora_manana.pack(side="left", padx=5)

        ctk.CTkLabel(
            fr_manana, text="Tolerancia (min):", text_color=TM.text_secondary()
        ).pack(side="left", padx=(20, 5))

        self.entry_tolerancia_manana = ctk.CTkEntry(
            fr_manana,
            width=60,
            placeholder_text="10",
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        self.entry_tolerancia_manana.pack(side="left", padx=5)

        # Turno tarde
        fr_tarde = ctk.CTkFrame(fr_academico, fg_color=TM.bg_card(), corner_radius=10)
        fr_tarde.pack(fill="x", pady=5)

        ctk.CTkLabel(
            fr_tarde,
            text="🌆 Turno Tarde",
            font=("Roboto", 12, "bold"),
            text_color=TM.text(),
        ).pack(side="left", padx=20, pady=15)

        ctk.CTkLabel(
            fr_tarde, text="Hora de entrada:", text_color=TM.text_secondary()
        ).pack(side="left", padx=(50, 5))

        self.entry_hora_tarde = ctk.CTkEntry(
            fr_tarde,
            width=80,
            placeholder_text="14:00",
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        self.entry_hora_tarde.pack(side="left", padx=5)

        ctk.CTkLabel(
            fr_tarde, text="Tolerancia (min):", text_color=TM.text_secondary()
        ).pack(side="left", padx=(20, 5))

        self.entry_tolerancia_tarde = ctk.CTkEntry(
            fr_tarde,
            width=60,
            placeholder_text="10",
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        self.entry_tolerancia_tarde.pack(side="left", padx=5)

        # Separador
        ctk.CTkFrame(fr_academico, height=2, fg_color=TM.bg_card()).pack(
            fill="x", pady=20
        )

        # Año académico
        ctk.CTkLabel(
            fr_academico,
            text="📅 PERIODO ACADÉMICO",
            font=("Roboto", 14, "bold"),
            text_color=TM.primary(),
            anchor="w",
        ).pack(fill="x", pady=(0, 15))

        fr_periodo = ctk.CTkFrame(fr_academico, fg_color=TM.bg_card(), corner_radius=10)
        fr_periodo.pack(fill="x", pady=5)

        ctk.CTkLabel(
            fr_periodo, text="Año Actual:", text_color=TM.text_secondary()
        ).pack(side="left", padx=20, pady=15)

        self.entry_anio = ctk.CTkEntry(
            fr_periodo,
            width=100,
            placeholder_text="2026",
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        self.entry_anio.pack(side="left", padx=5)

        ctk.CTkLabel(
            fr_periodo, text="Periodo:", text_color=TM.text_secondary()
        ).pack(side="left", padx=(30, 5))

        self.combo_periodo = ctk.CTkComboBox(
            fr_periodo,
            values=["I", "II", "ANUAL"],
            width=100,
            state="readonly",
            fg_color=TM.bg_main(),
            dropdown_fg_color=TM.bg_panel(),
            button_color=TM.primary(),
            button_hover_color=TM.hover(),
            text_color=TM.text(),
        )
        self.combo_periodo.set("I")
        self.combo_periodo.pack(side="left", padx=5)

    def _crear_tab_codigos(self):
        """PESTAÑA 3: CÓDIGOS DE MATRÍCULA"""
        tab3 = self.tabview.tab("🔢 Códigos de Matrícula")
        fr_codigos = ctk.CTkFrame(tab3, fg_color="transparent")
        fr_codigos.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(
            fr_codigos,
            text="🎫 CONFIGURACIÓN DE CÓDIGOS",
            font=("Roboto", 14, "bold"),
            text_color=TM.primary(),
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            fr_codigos,
            text="Los códigos se generan automáticamente al registrar alumnos",
            text_color=TM.text_secondary(),
            font=("Roboto", 10),
        ).pack(anchor="w", pady=(0, 20))

        # Formato
        fr_formato = ctk.CTkFrame(fr_codigos, fg_color=TM.bg_card(), corner_radius=10)
        fr_formato.pack(fill="x", pady=10)

        ctk.CTkLabel(
            fr_formato, text="Prefijo del código:", text_color=TM.text_secondary()
        ).pack(side="left", padx=20, pady=20)

        self.entry_prefijo = ctk.CTkEntry(
            fr_formato,
            width=100,
            placeholder_text="POA",
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        self.entry_prefijo.pack(side="left", padx=5)

        ctk.CTkLabel(
            fr_formato,
            text="+ AÑO (2 dígitos) + CONSECUTIVO (5 dígitos)",
            text_color=TM.text_secondary(),
        ).pack(side="left", padx=20)

        # Vista previa
        fr_preview = ctk.CTkFrame(fr_codigos, fg_color=TM.bg_main(), corner_radius=10)
        fr_preview.pack(fill="x", pady=10)

        ctk.CTkLabel(
            fr_preview, text="👁️ Vista Previa:", text_color=TM.text_secondary()
        ).pack(side="left", padx=20, pady=20)

        self.lbl_preview_codigo = ctk.CTkLabel(
            fr_preview,
            text="POA260001",
            font=("Roboto Mono", 18, "bold"),
            text_color=TM.primary(),
        )
        self.lbl_preview_codigo.pack(side="left", padx=10)

        self.entry_prefijo.bind("<KeyRelease>", self.actualizar_preview_codigo)

        # Contador actual
        fr_contador = ctk.CTkFrame(fr_codigos, fg_color=TM.bg_card(), corner_radius=10)
        fr_contador.pack(fill="x", pady=10)

        ctk.CTkLabel(
            fr_contador,
            text="Siguiente número disponible:",
            text_color=TM.text_secondary(),
        ).pack(side="left", padx=20, pady=20)

        self.entry_contador = ctk.CTkEntry(
            fr_contador,
            width=100,
            placeholder_text="1",
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        self.entry_contador.pack(side="left", padx=5)

        ctk.CTkLabel(
            fr_contador,
            text="⚠️ Modificar solo si migró datos de otro sistema",
            text_color=TM.warning(),
            font=("Roboto", 9),
        ).pack(side="left", padx=20)

    def _crear_tab_apariencia(self):
        """PESTAÑA 4: APARIENCIA"""
        tab4 = self.tabview.tab("🎨 Apariencia")
        fr_apariencia = ctk.CTkFrame(tab4, fg_color="transparent")
        fr_apariencia.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(
            fr_apariencia,
            text="🎨 PERSONALIZACIÓN VISUAL",
            font=("Roboto", 14, "bold"),
            text_color=TM.primary(),
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            fr_apariencia,
            text="⚠️ Funcionalidad disponible en la versión 2.0",
            text_color=TM.text_secondary(),
            font=("Roboto", 11),
        ).pack(anchor="w", pady=20)

        # Preview de colores (bloqueado)
        fr_colores = ctk.CTkFrame(fr_apariencia, fg_color=TM.bg_card(), corner_radius=10)
        fr_colores.pack(fill="x", pady=10)

        ctk.CTkLabel(
            fr_colores, text="Color primario:", text_color=TM.text_secondary()
        ).pack(side="left", padx=20, pady=20)

        ctk.CTkFrame(
            fr_colores, width=50, height=30, fg_color=TM.primary(), corner_radius=5
        ).pack(side="left", padx=5)

        ctk.CTkLabel(
            fr_colores,
            text="(Próximamente)",
            text_color=TM.text_muted(),
            font=("Roboto", 9),
        ).pack(side="left", padx=10)

    def _crear_botones_finales(self):
        """Botones de acción"""
        fr_botones = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        fr_botones.pack(fill="x", pady=(20, 0))

        self.btn_restaurar = ctk.CTkButton(
            fr_botones,
            text="🔄 Restaurar Valores",
            height=50,
            fg_color=TM.bg_card(),
            hover_color=TM.hover(),
            text_color=TM.text(),
            command=self.cargar_configuracion,
        )
        self.btn_restaurar.pack(side="right", padx=5)

        self.btn_guardar = ctk.CTkButton(
            fr_botones,
            text="💾 GUARDAR CAMBIOS",
            height=50,
            font=("Roboto", 14, "bold"),
            fg_color=TM.success(),
            hover_color="#2ecc71",
            command=self.guardar_configuracion,
        )
        self.btn_guardar.pack(side="right", padx=5)

    # =================== MÉTODOS UI HELPERS ===================

    def campo(self, parent, label, placeholder=""):
        """Campo de entrada estándar"""
        fr = ctk.CTkFrame(parent, fg_color="transparent")
        fr.pack(fill="x", pady=5)

        ctk.CTkLabel(
            fr, text=label, anchor="w", text_color=TM.text_secondary()
        ).pack(fill="x")

        entry = ctk.CTkEntry(
            fr,
            placeholder_text=placeholder,
            height=40,
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        entry.pack(fill="x")
        return entry

    def cargar_logo(self):
        """Cargar imagen de logo"""
        filepath = filedialog.askopenfilename(
            title="Seleccionar Logo",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
            ],
        )
        if not filepath:
            return

        if os.path.getsize(filepath) > 2 * 1024 * 1024:
            messagebox.showwarning("Archivo muy grande", "El logo no debe superar 2MB")
            return

        try:
            img = Image.open(filepath)
            img.thumbnail((140, 140), Image.Resampling.LANCZOS)

            self.logo_path = filepath
            self.logo_image = ctk.CTkImage(light_image=img, size=(140, 140))

            self.lbl_logo.configure(image=self.logo_image, text="")
            self.btn_eliminar_logo.configure(state="normal")

            messagebox.showinfo(
                "✅ Logo Cargado",
                "Logo cargado correctamente\n\n⚠️ Recuerda guardar los cambios",
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el logo:\n{e}")

    def eliminar_logo(self):
        """Eliminar logo actual"""
        if messagebox.askyesno("Confirmar", "¿Eliminar el logo actual?"):
            self.logo_path = None
            self.logo_image = None
            self.lbl_logo.configure(image=None, text="🏫\nSin Logo")
            self.btn_eliminar_logo.configure(state="disabled")

    def actualizar_preview_codigo(self, event):
        """Actualizar vista previa del código"""
        prefijo = self.entry_prefijo.get().upper()[:3]
        anio = "26"
        numero = "00001"
        preview = f"{prefijo}{anio}{numero}"
        self.lbl_preview_codigo.configure(text=preview)

    def cargar_configuracion(self):
        """Cargar configuración actual desde BD"""
        self.entry_nombre.insert(0, "INSTITUCIÓN EDUCATIVA MUSUQ")
        self.entry_nombre_corto.insert(0, "I.E. MUSUQ")
        self.entry_ruc.insert(0, "20123456789")
        self.entry_director.insert(0, "")
        self.entry_direccion.insert(0, "Av. Principal 123, Lima")
        self.entry_telefono.insert(0, "(01) 123-4567")
        self.entry_email.insert(0, "contacto@musuq.edu.pe")
        self.entry_hora_manana.insert(0, "08:00")
        self.entry_tolerancia_manana.insert(0, "10")
        self.entry_hora_tarde.insert(0, "14:00")
        self.entry_tolerancia_tarde.insert(0, "10")
        self.entry_anio.insert(0, "2026")
        self.entry_prefijo.insert(0, "POA")
        self.entry_contador.insert(0, "1")

    def guardar_configuracion(self):
        """Validar y guardar configuración"""
        nombre = self.entry_nombre.get().strip()
        nombre_corto = self.entry_nombre_corto.get().strip()

        if not nombre or not nombre_corto:
            messagebox.showwarning("Validación", "Complete los campos obligatorios (*)")
            return

        try:
            hora_m = self.entry_hora_manana.get()
            hora_t = self.entry_hora_tarde.get()
            if not (len(hora_m) == 5 and ":" in hora_m):
                raise ValueError("Formato de hora inválido")
            if not (len(hora_t) == 5 and ":" in hora_t):
                raise ValueError("Formato de hora inválido")
        except:
            messagebox.showwarning(
                "Validación", "Formato de hora inválido. Use HH:MM (ej: 08:00)"
            )
            return

        config_data = {
            "nombre": nombre,
            "nombre_corto": nombre_corto,
            "ruc": self.entry_ruc.get(),
            "director": self.entry_director.get(),
            "direccion": self.entry_direccion.get(),
            "telefono": self.entry_telefono.get(),
            "email": self.entry_email.get(),
            "logo_path": self.logo_path,
            "hora_entrada_manana": hora_m,
            "tolerancia_manana": self.entry_tolerancia_manana.get(),
            "hora_entrada_tarde": hora_t,
            "tolerancia_tarde": self.entry_tolerancia_tarde.get(),
            "anio_actual": self.entry_anio.get(),
            "periodo_actual": self.combo_periodo.get(),
            "prefijo_codigo": self.entry_prefijo.get().upper(),
            "contador_matriculas": self.entry_contador.get(),
        }

        messagebox.showinfo(
            "✅ Guardado",
            f"Configuración guardada correctamente:\n\n"
            f"Institución: {nombre}\n"
            f"RUC: {config_data['ruc']}\n"
            f"Periodo: {config_data['anio_actual']}-{config_data['periodo_actual']}\n\n"
            f"(Funcionalidad de guardado pendiente)",
        )
