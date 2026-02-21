import customtkinter as ctk
from app.controllers.auth_controller import AuthController

class LoginWindow(ctk.CTkToplevel):
    def __init__(self, master, on_login_success):
        super().__init__(master)
        self.on_login_success = on_login_success
        self.controller = AuthController()

        # Configuración de ventana independiente
        self.title("Iniciar Sesión - MUSUQ CLOUD")
        self.geometry("400x500")
        self.resizable(False, False)
        
        # Centrar en pantalla (opcional, pero recomendado)
        # self.eval('tk::PlaceWindow . center') # Truco rápido en algunas versiones, pero mejor manual:
        self.after(10, self.centrar_ventana)

        # Configuración de apariencia
        self.configure(fg_color="#2b2b2b") # Color de fondo agradable para la ventana

        # Protocolo de cierre: Si cierran el login, cierran la app
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # ============================================================
        # CARD PRINCIPAL
        # ============================================================
        self.card = ctk.CTkFrame(self, width=360, corner_radius=15, fg_color="transparent")
        self.card.pack(padx=20, pady=20, expand=True, fill="both")
        
        # --- HEADER ---
        # Logo / Título
        ctk.CTkLabel(
            self.card,
            text="🎓 MUSUQ CLOUD",
            font=("Roboto", 30, "bold")
        ).pack(pady=(30, 10))
        
        ctk.CTkLabel(
            self.card,
            text="Sistema de Gestión Educativa",
            font=("Roboto", 14),
            text_color="gray"
        ).pack(pady=(0, 30))

        # --- FORMULARIO ---
        # Campo: Usuario
        self.entry_user = ctk.CTkEntry(
            self.card,
            placeholder_text="👤 Usuario",
            width=280,
            height=40,
            font=("Roboto", 14)
        )
        self.entry_user.pack(pady=10)
        self.entry_user.bind("<Return>", self.intentar_login)
        
        # Campo: Contraseña
        self.entry_pass = ctk.CTkEntry(
            self.card,
            placeholder_text="🔒 Contraseña",
            show="*",
            width=280,
            height=40,
            font=("Roboto", 14)
        )
        self.entry_pass.pack(pady=10)
        self.entry_pass.bind("<Return>", self.intentar_login)

        # Opcional: Checkbox Recordar (Visual por ahora)
        self.chk_recordar = ctk.CTkCheckBox(
            self.card, 
            text="Recordar sesión",
            font=("Roboto", 12),
            checkbox_height=18,
            checkbox_width=18
        )
        self.chk_recordar.pack(pady=5)

        # --- BOTÓN DE ACCIÓN ---
        self.btn_login = ctk.CTkButton(
            self.card,
            text="INICIAR SESIÓN",
            width=280,
            height=40,
            font=("Roboto", 14, "bold"),
            fg_color="#1f6aa5",
            hover_color="#144870",
            command=self.intentar_login
        )
        self.btn_login.pack(pady=20)

        # Mensaje de error (oculto inicialmente)
        self.lbl_mensaje = ctk.CTkLabel(
            self.card, 
            text="", 
            text_color="#e74c3c", 
            font=("Roboto", 12)
        )
        self.lbl_mensaje.pack(pady=(0, 10))

        # --- FOOTER ---
        self.lbl_footer = ctk.CTkLabel(
            self.card,
            text="v1.0.0 | Powered by Python + CustomTkinter",
            font=("Roboto", 10),
            text_color="gray"
        )
        self.lbl_footer.pack(side="bottom", pady=10)
        
        # Hacer focus
        self.focus_force()

    def centrar_ventana(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _on_closing(self):
        """Si cierran el login sin loguearse, cerramos toda la app"""
        self.master.destroy()

    def intentar_login(self, event=None):
        """
        Maneja el intento de inicio de sesión
        """
        usuario = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        
        # Reset mensaje
        self.lbl_mensaje.configure(text="")

        if not usuario or not password:
             self.lbl_mensaje.configure(text="Por favor complete todos los campos")
             return

        # Feedback visual
        self.btn_login.configure(state="disabled", text="Verificando...")
        self.update()

        try:
            exito, mensaje, user_obj = self.controller.login(usuario, password)

            if exito:
                self.lbl_mensaje.configure(text="¡Bienvenido!", text_color="#2ecc71")
                # Éxito: Llamamos al callback y cerramos esta ventana
                self.after(500, lambda: self._finalizar_login(user_obj))
            else:
                self.lbl_mensaje.configure(text=mensaje, text_color="#e74c3c")
                self.btn_login.configure(state="normal", text="INICIAR SESIÓN")
        except Exception as e:
            self.lbl_mensaje.configure(text=f"Error: {e}", text_color="#e74c3c")
            self.btn_login.configure(state="normal", text="INICIAR SESIÓN")

    def _finalizar_login(self, user_obj):
        self.on_login_success(user_obj)
        self.destroy()