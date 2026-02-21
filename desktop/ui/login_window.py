"""
Ventana de Login
Sistema Musuq Cloud
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Optional
import threading

from core.config import Config
from core.api_client import AuthClient
from core.auth_manager import AuthManager
from core.theme_manager import ThemeManager as TM


class LoginWindow(ctk.CTkToplevel):
    """Ventana de login moderna y profesional"""
    
    def __init__(self, parent, on_login_success: Callable):
        super().__init__(parent)
        
        self.parent = parent
        self.on_login_success = on_login_success
        self.auth_client = AuthClient()
        self.auth_manager = AuthManager()
        
        # Configurar ventana
        self.title(f"{Config.APP_NAME} - Iniciar Sesión")
        self.geometry(Config.LOGIN_SIZE)
        self.resizable(False, True)
        
        # Hacer modal
        self.transient(parent)
        self.grab_set()
        
        # Centrar ventana
        self.after(10, self.center_window)
        
        # Configurar fondo
        self.configure(fg_color=TM.bg_main())
        
        # Crear UI
        self.create_widgets()
        
        # Verificar sesión guardada
        self.after(500, self.check_saved_session)
        
        # Focus en usuario
        self.after(100, lambda: self.entry_username.focus())
    
    def center_window(self):
        """Centrar ventana en la pantalla"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Crear todos los widgets de la UI"""
        
        # ==================== FRAME PRINCIPAL ====================
        main_frame = ctk.CTkFrame(
            self, 
            corner_radius=20,
            fg_color=TM.bg_card()
        )
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        # ==================== LOGO Y TÍTULO ====================
        logo_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        logo_frame.pack(pady=(40, 10))
        
        # Logo emoji grande
        ctk.CTkLabel(
            logo_frame,
            text="🎓",
            font=ctk.CTkFont(size=50)
        ).pack()
        
        # Nombre de la app
        ctk.CTkLabel(
            logo_frame,
            text="MUSUQ CLOUD",
            font=ctk.CTkFont(family="Roboto", size=32, weight="bold"),
            text_color=TM.text()
        ).pack(pady=(5, 0))
        
        # Subtítulo
        ctk.CTkLabel(
            main_frame,
            text="Sistema de Gestión Educativa",
            font=ctk.CTkFont(family="Roboto", size=14),
            text_color=TM.text_secondary()
        ).pack(pady=(0, 35))
        
        # ==================== CAMPOS DE ENTRADA ====================
        
        # Usuario
        self.entry_username = ctk.CTkEntry(
            main_frame,
            placeholder_text="👤  Usuario",
            width=320,
            height=45,
            font=ctk.CTkFont(family="Roboto", size=14),
            corner_radius=10,
            fg_color=TM.bg_panel(),
            border_color=TM.get_theme().border
        )
        self.entry_username.pack(pady=8)
        self.entry_username.bind("<Return>", lambda e: self.entry_password.focus())
        
        # Contraseña
        self.entry_password = ctk.CTkEntry(
            main_frame,
            placeholder_text="🔒  Contraseña",
            show="•",
            width=320,
            height=45,
            font=ctk.CTkFont(family="Roboto", size=14),
            corner_radius=10,
            fg_color=TM.bg_panel(),
            border_color=TM.get_theme().border
        )
        self.entry_password.pack(pady=8)
        self.entry_password.bind("<Return>", lambda e: self.handle_login())
        
        # ==================== RECORDAR SESIÓN ====================
        self.remember_var = ctk.BooleanVar(value=False)
        self.checkbox_remember = ctk.CTkCheckBox(
            main_frame,
            text="Recordar sesión",
            variable=self.remember_var,
            font=ctk.CTkFont(family="Roboto", size=12),
            text_color=TM.text_secondary(),
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=5
        )
        self.checkbox_remember.pack(pady=(10, 20))
        
        # ==================== BOTÓN LOGIN ====================
        self.btn_login = ctk.CTkButton(
            main_frame,
            text="INICIAR SESIÓN",
            width=320,
            height=45,
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
            corner_radius=10,
            fg_color="#1f6aa5",
            hover_color="#144870",
            command=self.handle_login
        )
        self.btn_login.pack(pady=5)
        
        # ==================== MENSAJE DE ERROR ====================
        self.lbl_error = ctk.CTkLabel(
            main_frame,
            text="",
            font=ctk.CTkFont(family="Roboto", size=12),
            text_color=TM.danger(),
            wraplength=300
        )
        self.lbl_error.pack(pady=(10, 0))
        
        # ==================== ESTADO DE CONEXIÓN ====================
        self.lbl_status = ctk.CTkLabel(
            main_frame,
            text="",
            font=ctk.CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary()
        )
        self.lbl_status.pack(pady=(5, 0))
        
        # ==================== FOOTER ====================
        footer_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer_frame.pack(side="bottom", pady=15)
        
        ctk.CTkLabel(
            footer_frame,
            text=f"v{Config.APP_VERSION} • Powered by FastAPI + CustomTkinter",
            font=ctk.CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary()
        ).pack()
    
    def check_saved_session(self):
        """Verificar si hay una sesión guardada"""
        if self.auth_manager.load_session():
            self.lbl_status.configure(
                text="🔄 Verificando sesión guardada...",
                text_color=TM.primary()
            )
            self.update()
            
            # Verificar token en background
            self.auth_client.token = self.auth_manager.token
            
            def verify():
                if self.auth_client.verify_token():
                    self.after(0, self.auto_login)
                else:
                    self.after(0, self.session_expired)
            
            thread = threading.Thread(target=verify, daemon=True)
            thread.start()
    
    def auto_login(self):
        """Auto-login con sesión guardada"""
        self.lbl_status.configure(
            text="✅ Sesión restaurada",
            text_color=TM.success()
        )
        self.after(500, lambda: self.login_success(self.auth_manager.user_data))
    
    def session_expired(self):
        """Sesión expirada"""
        self.lbl_status.configure(
            text="⚠️ Sesión expirada. Por favor inicie sesión nuevamente.",
            text_color=TM.warning()
        )
        self.auth_manager.clear_session()
    
    def handle_login(self):
        """Manejar intento de login"""
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        
        # Validaciones
        if not username or not password:
            self.show_error("Por favor complete todos los campos")
            return
        
        # Deshabilitar UI
        self.set_loading(True)
        self.lbl_error.configure(text="")
        
        # Login en background
        def do_login():
            success, message, user_data = self.auth_client.login(username, password)
            self.after(0, lambda: self.handle_login_result(success, message, user_data))
        
        thread = threading.Thread(target=do_login, daemon=True)
        thread.start()
    
    def handle_login_result(self, success: bool, message: str, user_data: Optional[dict]):
        """Manejar resultado del login"""
        self.set_loading(False)
        
        if success:
            # Guardar sesión
            self.auth_manager.save_session(
                token=self.auth_client.token,
                user_data=user_data or {},
                remember=self.remember_var.get()
            )
            self.login_success(user_data)
        else:
            self.show_error(message)
    
    def login_success(self, user_data: Optional[dict]):
        """Login exitoso"""
        self.lbl_error.configure(
            text=f"✅ ¡Bienvenido, {user_data.get('nombre_completo', 'Usuario') if user_data else 'Usuario'}!",
            text_color=TM.success()
        )
        self.update()
        
        # Pequeño delay para mostrar mensaje
        self.after(800, lambda: self.finish_login(user_data))
    
    def finish_login(self, user_data: Optional[dict]):
        """Finalizar login y abrir main window"""
        self.grab_release()
        self.destroy()
        self.on_login_success(self.auth_client, user_data or {})
    
    def show_error(self, message: str):
        """Mostrar mensaje de error"""
        self.lbl_error.configure(text=f"❌ {message}", text_color=TM.danger())
    
    def set_loading(self, loading: bool):
        """Activar/desactivar estado de carga"""
        if loading:
            self.btn_login.configure(
                state="disabled",
                text="⏳ Iniciando sesión..."
            )
            self.entry_username.configure(state="disabled")
            self.entry_password.configure(state="disabled")
        else:
            self.btn_login.configure(
                state="normal",
                text="INICIAR SESIÓN"
            )
            self.entry_username.configure(state="normal")
            self.entry_password.configure(state="normal")
