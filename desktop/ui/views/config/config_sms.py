"""
ConfigSMSView - VERSIÓN VISUAL PREMIUM (Musuq Cloud)
Configuración de notificaciones SMS refactorizada con ThemeManager.
"""

import customtkinter as ctk
from tkinter import messagebox
import threading
import winsound

from core.theme_manager import TM


class ConfigSMSView(ctk.CTkFrame):
    """
    Panel de configuración de notificaciones SMS.
    TODO: Conectar con backend cuando esté listo.
    """

    def __init__(self, parent, auth_client=None):
        super().__init__(parent, fg_color=TM.bg_main())

        # Variables de estado (mock data)
        self.proveedor_var = ctk.StringVar(value="twilio")
        self.mostrar_token = False

        # Construir UI
        self._crear_interfaz()

        # Cargar datos de ejemplo
        self._cargar_datos_mock()

    def _crear_interfaz(self):
        """Construye toda la interfaz"""
        # Contenedor principal con scroll
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=TM.bg_main(),
            scrollbar_button_color=TM.bg_card(),
            scrollbar_button_hover_color=TM.hover(),
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ENCABEZADO
        self._crear_encabezado()

        # SECCIÓN: PROVEEDOR
        self._crear_seccion_proveedor()

        # SECCIÓN: CREDENCIALES
        self._crear_seccion_credenciales()

        # SECCIÓN: TIPOS DE NOTIFICACIÓN
        self._crear_seccion_notificaciones()

        # SECCIÓN: CONFIGURACIÓN DE HORARIOS
        self._crear_seccion_horarios()

        # SECCIÓN: PLANTILLAS
        self._crear_seccion_plantillas()

        # SECCIÓN: ESTADÍSTICAS
        self._crear_seccion_estadisticas()

        # BOTONES PRINCIPALES
        self._crear_botones_principales()

    def _crear_encabezado(self):
        """Encabezado con título"""
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        titulo = ctk.CTkLabel(
            header_frame,
            text="⚙️ CONFIGURACIÓN SMS",
            font=("Roboto", 24, "bold"),
            text_color=TM.text(),
        )
        titulo.pack(anchor="w")

        subtitulo = ctk.CTkLabel(
            header_frame,
            text="Configure el sistema de mensajería automática a apoderados",
            font=("Roboto", 13),
            text_color=TM.text_secondary(),
        )
        subtitulo.pack(anchor="w", pady=(5, 0))

    def _crear_seccion_proveedor(self):
        """Sección de selección de proveedor"""
        frame = self._crear_card("📱 PROVEEDOR DE SMS")

        # Radio buttons para proveedores
        providers_frame = ctk.CTkFrame(frame, fg_color=TM.bg_main(), corner_radius=8)
        providers_frame.pack(fill="x", padx=10, pady=10)

        proveedores = [
            ("Twilio", "twilio", "#F22F46"),
            ("AWS SNS", "aws", "#FF9900"),
            ("Gateway Local", "gateway_local", TM.success()),
        ]

        for idx, (nombre, valor, color) in enumerate(proveedores):
            radio = ctk.CTkRadioButton(
                providers_frame,
                text=nombre,
                variable=self.proveedor_var,
                value=valor,
                font=("Roboto", 14),
                text_color=TM.text(),
                fg_color=color,
                hover_color=color,
                command=self._cambiar_proveedor,
            )
            radio.pack(side="left", padx=20, pady=10)

    def _crear_seccion_credenciales(self):
        """Sección de credenciales Twilio"""
        frame = self._crear_card("🔑 CREDENCIALES TWILIO")

        # Account SID (placeholder, no real)
        self._crear_campo_config(
            frame,
            "Account SID:",
            "TWILIO_ACCOUNT_SID_AQUI",
            "entry_sid",
            boton_texto="Validar",
            boton_comando=self._validar_credenciales,
        )

        # Auth Token (oculto)
        token_frame = ctk.CTkFrame(frame, fg_color="transparent")
        token_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            token_frame,
            text="Auth Token:",
            font=("Roboto", 13),
            text_color=TM.text_secondary(),
            width=150,
            anchor="w",
        ).pack(side="left", padx=(0, 10))

        self.entry_token = ctk.CTkEntry(
            token_frame,
            placeholder_text="••••••••••••••••••••",
            font=("Roboto", 12),
            height=35,
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
            show="•",
        )
        self.entry_token.pack(side="left", fill="x", expand=True, padx=(0, 10))
        # No poner token real por defecto
        self.entry_token.insert(0, "")

        btn_mostrar = ctk.CTkButton(
            token_frame,
            text="🔓 Mostrar",
            width=100,
            height=35,
            font=("Roboto", 12),
            fg_color=TM.bg_card(),
            hover_color=TM.hover(),
            command=self._toggle_token,
        )
        btn_mostrar.pack(side="left")

        # Teléfono
        self._crear_campo_config(
            frame,
            "Teléfono Emisor:",
            "+51 999 888 777",
            "entry_phone",
            boton_texto="📞 Probar",
            boton_comando=self._probar_sms,
        )

    def _crear_seccion_notificaciones(self):
        """Sección de tipos de notificación"""
        frame = self._crear_card("✉️ TIPOS DE NOTIFICACIÓN")

        notif_frame = ctk.CTkFrame(frame, fg_color=TM.bg_main(), corner_radius=8)
        notif_frame.pack(fill="x", padx=10, pady=10)

        # Checkboxes
        self.check_puntual = ctk.CTkCheckBox(
            notif_frame,
            text="✅ Enviar SMS al marcar PUNTUAL",
            font=("Roboto", 13),
            text_color=TM.text(),
            fg_color=TM.success(),
            hover_color="#45a049",
        )
        self.check_puntual.pack(anchor="w", padx=20, pady=8)
        self.check_puntual.select()

        self.check_tardanza = ctk.CTkCheckBox(
            notif_frame,
            text="⚠️ Enviar SMS al marcar TARDANZA",
            font=("Roboto", 13),
            text_color=TM.text(),
            fg_color=TM.warning(),
            hover_color="#F57C00",
        )
        self.check_tardanza.pack(anchor="w", padx=20, pady=8)
        self.check_tardanza.select()

        self.check_inasistencia = ctk.CTkCheckBox(
            notif_frame,
            text="❌ Enviar SMS por INASISTENCIA (al cerrar turno)",
            font=("Roboto", 13),
            text_color=TM.text(),
            fg_color=TM.danger(),
            hover_color="#D32F2F",
        )
        self.check_inasistencia.pack(anchor="w", padx=20, pady=8)

        self.check_deuda = ctk.CTkCheckBox(
            notif_frame,
            text="💰 Enviar SMS por DEUDA VENCIDA",
            font=("Roboto", 13),
            text_color=TM.text(),
            fg_color="#9C27B0",
            hover_color="#7B1FA2",
        )
        self.check_deuda.pack(anchor="w", padx=20, pady=8)

    def _crear_seccion_horarios(self):
        """Sección de configuración de horarios"""
        frame = self._crear_card("⏰ CONFIGURACIÓN DE HORARIOS")

        # Hora de alerta inasistencia
        hora_frame = ctk.CTkFrame(frame, fg_color="transparent")
        hora_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            hora_frame,
            text="Hora de alerta inasistencia:",
            font=("Roboto", 13),
            text_color=TM.text_secondary(),
            width=250,
            anchor="w",
        ).pack(side="left", padx=(0, 10))

        self.combo_hora = ctk.CTkComboBox(
            hora_frame,
            values=["10:00", "11:00", "12:00", "13:00", "14:00"],
            font=("Roboto", 12),
            width=150,
            height=35,
            fg_color=TM.bg_main(),
            dropdown_fg_color=TM.bg_panel(),
            button_color=TM.primary(),
            button_hover_color=TM.hover(),
            text_color=TM.text(),
        )
        self.combo_hora.pack(side="left")
        self.combo_hora.set("12:00")

        # Máximo SMS por hora
        max_frame = ctk.CTkFrame(frame, fg_color="transparent")
        max_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            max_frame,
            text="Máximo SMS por hora:",
            font=("Roboto", 13),
            text_color=TM.text_secondary(),
            width=250,
            anchor="w",
        ).pack(side="left", padx=(0, 10))

        self.entry_max_sms = ctk.CTkEntry(
            max_frame,
            placeholder_text="300",
            font=("Roboto", 12),
            width=150,
            height=35,
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        self.entry_max_sms.pack(side="left")
        self.entry_max_sms.insert(0, "300")

    def _crear_seccion_plantillas(self):
        """Sección de personalización de mensajes"""
        frame = self._crear_card("📝 PERSONALIZAR MENSAJES")

        btn_plantillas = ctk.CTkButton(
            frame,
            text="✏️ Editar Plantillas de Mensajes",
            font=("Roboto", 14, "bold"),
            height=40,
            fg_color=TM.primary(),
            hover_color=TM.hover(),
            command=self._editar_plantillas,
        )
        btn_plantillas.pack(padx=10, pady=10)

        # Preview de plantilla
        preview_frame = ctk.CTkFrame(frame, fg_color=TM.bg_card(), corner_radius=8)
        preview_frame.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(
            preview_frame,
            text="Vista previa (Puntual):",
            font=("Roboto", 11, "bold"),
            text_color=TM.text_muted(),
        ).pack(anchor="w", padx=10, pady=(10, 5))

        preview_text = ctk.CTkLabel(
            preview_frame,
            text="MUSUQ: Su hijo/a Juan Pérez ingresó a las 08:15 (Puntual). 30/01/2026",
            font=("Roboto", 11),
            text_color=TM.text(),
            wraplength=600,
            justify="left",
        )
        preview_text.pack(anchor="w", padx=10, pady=(0, 10))

    def _crear_seccion_estadisticas(self):
        """Sección de estadísticas"""
        frame = self._crear_card("📊 ESTADÍSTICAS (Último mes)")

        # Tabla de estadísticas
        tabla_frame = ctk.CTkFrame(frame, fg_color=TM.bg_card(), corner_radius=8)
        tabla_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Encabezados
        headers = ["Tipo", "Enviados", "Costo"]
        col_widths = [200, 100, 120]

        header_frame = ctk.CTkFrame(tabla_frame, fg_color=TM.hover(), corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)

        for header, width in zip(headers, col_widths):
            ctk.CTkLabel(
                header_frame,
                text=header,
                font=("Roboto", 12, "bold"),
                text_color=TM.text(),
                width=width,
                anchor="center",
            ).pack(side="left", padx=5, pady=10)

        # Datos de ejemplo
        datos = [
            ("📱 Asistencia", "3,520", "S/. 668.80", TM.success()),
            ("❌ Inasistencia", "880", "S/. 167.20", TM.danger()),
            ("💰 Deuda", "440", "S/. 83.60", "#9C27B0"),
        ]

        for tipo, enviados, costo, color in datos:
            row_frame = ctk.CTkFrame(tabla_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=0, pady=2)

            ctk.CTkLabel(
                row_frame,
                text=tipo,
                font=("Roboto", 11),
                text_color=color,
                width=200,
                anchor="w",
            ).pack(side="left", padx=10)

            ctk.CTkLabel(
                row_frame,
                text=enviados,
                font=("Roboto", 11),
                text_color=TM.text(),
                width=100,
                anchor="center",
            ).pack(side="left", padx=5)

            ctk.CTkLabel(
                row_frame,
                text=costo,
                font=("Roboto", 11, "bold"),
                text_color=TM.text(),
                width=120,
                anchor="center",
            ).pack(side="left", padx=5)

        # Separador
        separator = ctk.CTkFrame(tabla_frame, fg_color=TM.hover(), height=2)
        separator.pack(fill="x", padx=10, pady=10)

        # Total
        total_frame = ctk.CTkFrame(tabla_frame, fg_color="transparent")
        total_frame.pack(fill="x", padx=0, pady=(0, 10))

        ctk.CTkLabel(
            total_frame,
            text="TOTAL",
            font=("Roboto", 12, "bold"),
            text_color=TM.warning(),
            width=200,
            anchor="w",
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            total_frame,
            text="4,840",
            font=("Roboto", 12, "bold"),
            text_color=TM.warning(),
            width=100,
            anchor="center",
        ).pack(side="left", padx=5)

        ctk.CTkLabel(
            total_frame,
            text="S/. 919.60",
            font=("Roboto", 12, "bold"),
            text_color=TM.warning(),
            width=120,
            anchor="center",
        ).pack(side="left", padx=5)

    def _crear_botones_principales(self):
        """Botones de acción principales"""
        botones_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        botones_frame.pack(fill="x", pady=20)

        btn_guardar = ctk.CTkButton(
            botones_frame,
            text="💾 Guardar Configuración",
            font=("Roboto", 16, "bold"),
            height=50,
            fg_color=TM.success(),
            hover_color="#45a049",
            command=self._guardar_configuracion,
        )
        btn_guardar.pack(side="left", padx=(0, 10), fill="x", expand=True)

        btn_prueba = ctk.CTkButton(
            botones_frame,
            text="🧪 Enviar SMS de Prueba",
            font=("Roboto", 16, "bold"),
            height=50,
            fg_color=TM.primary(),
            hover_color=TM.hover(),
            command=self._enviar_sms_prueba,
        )
        btn_prueba.pack(side="left", fill="x", expand=True)

    # ========== MÉTODOS AUXILIARES ==========

    def _crear_card(self, titulo):
        """Crea una tarjeta con título"""
        card = ctk.CTkFrame(self.scroll_frame, fg_color=TM.bg_panel(), corner_radius=10)
        card.pack(fill="x", pady=(0, 15))

        titulo_label = ctk.CTkLabel(
            card,
            text=titulo,
            font=("Roboto", 16, "bold"),
            text_color=TM.primary(),
        )
        titulo_label.pack(anchor="w", padx=15, pady=(15, 10))

        return card

    def _crear_campo_config(
        self, parent, label, placeholder, attr_name, boton_texto=None, boton_comando=None
    ):
        """Crea un campo de configuración con label, entry y botón opcional"""
        field_frame = ctk.CTkFrame(parent, fg_color="transparent")
        field_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            field_frame,
            text=label,
            font=("Roboto", 13),
            text_color=TM.text_secondary(),
            width=150,
            anchor="w",
        ).pack(side="left", padx=(0, 10))

        entry = ctk.CTkEntry(
            field_frame,
            placeholder_text=placeholder,
            font=("Roboto", 12),
            height=35,
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        entry.insert(0, placeholder)

        setattr(self, attr_name, entry)

        if boton_texto and boton_comando:
            btn = ctk.CTkButton(
                field_frame,
                text=boton_texto,
                width=100,
                height=35,
                font=("Roboto", 12),
                fg_color=TM.primary(),
                hover_color=TM.hover(),
                command=boton_comando,
            )
            btn.pack(side="left")

    def _cargar_datos_mock(self):
        """Carga datos de ejemplo"""
        pass  # Ya están cargados en los widgets

    # ========== EVENTOS (MOCK - SIN FUNCIONALIDAD REAL) ==========

    def _cambiar_proveedor(self):
        """Cambia proveedor de SMS"""
        messagebox.showinfo(
            "Proveedor Cambiado",
            f"Proveedor seleccionado: {self.proveedor_var.get()}\n\n(Funcionalidad pendiente de implementar)",
        )

    def _validar_credenciales(self):
        """Valida credenciales del proveedor"""
        self._mostrar_cargando("Validando credenciales...")
        threading.Timer(
            1.5,
            lambda: self._ocultar_cargando_y_mensaje(
                "Credenciales Válidas",
                "✅ Conexión establecida correctamente con Twilio",
            ),
        ).start()

    def _toggle_token(self):
        """Muestra/oculta el token"""
        self.mostrar_token = not self.mostrar_token
        if self.mostrar_token:
            self.entry_token.configure(show="")
        else:
            self.entry_token.configure(show="•")

    def _probar_sms(self):
        """Envía SMS de prueba"""
        self._mostrar_cargando("Enviando SMS de prueba...")
        threading.Timer(
            2,
            lambda: self._ocultar_cargando_y_mensaje(
                "SMS Enviado",
                "✅ SMS de prueba enviado correctamente\nID: msg_abc123xyz",
            ),
        ).start()

        # Pitido
        try:
            winsound.Beep(1000, 200)
        except:
            pass

    def _editar_plantillas(self):
        """Abre editor de plantillas"""
        messagebox.showinfo(
            "Editor de Plantillas",
            "Esta función abrirá un diálogo para editar las plantillas de mensajes.\n\n(Pendiente de implementar)",
        )

    def _guardar_configuracion(self):
        """Guarda la configuración"""
        self._mostrar_cargando("Guardando configuración...")
        threading.Timer(
            1,
            lambda: self._ocultar_cargando_y_mensaje(
                "Configuración Guardada",
                "✅ La configuración se guardó correctamente",
            ),
        ).start()

    def _enviar_sms_prueba(self):
        """Envía SMS de prueba a un número"""
        dialogo = ctk.CTkInputDialog(
            text="Ingrese el número de celular para la prueba:", title="SMS de Prueba"
        )

        numero = dialogo.get_input()
        if numero:
            self._mostrar_cargando(f"Enviando SMS a {numero}...")
            threading.Timer(
                2,
                lambda: self._ocultar_cargando_y_mensaje(
                    "SMS de Prueba Enviado",
                    f"✅ SMS enviado correctamente a {numero}\n\nMensaje: MUSUQ - Esto es una prueba del sistema",
                ),
            ).start()

    def _mostrar_cargando(self, mensaje):
        """Muestra mensaje de cargando"""
        # TODO: Implementar overlay de cargando
        print(f"⏳ {mensaje}")

    def _ocultar_cargando_y_mensaje(self, titulo, mensaje):
        """Oculta cargando y muestra mensaje"""
        messagebox.showinfo(titulo, mensaje)
