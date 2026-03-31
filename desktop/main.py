"""
Sistema Musuq Cloud - Cliente Desktop
Punto de entrada principal
"""

import customtkinter as ctk
import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from core.theme_manager import ThemeManager
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


def _install_customtkinter_scaling_guard():
    """Evita crash si CustomTkinter recibe un factor de escala 0."""
    try:
        from customtkinter.windows.widgets.scaling.scaling_base_class import CTkScalingBaseClass
    except Exception:
        return

    if getattr(CTkScalingBaseClass, "_musuq_scaling_guard_installed", False):
        return

    original_reverse_widget_scaling = CTkScalingBaseClass._reverse_widget_scaling
    original_reverse_window_scaling = CTkScalingBaseClass._reverse_window_scaling

    def _safe_reverse_widget_scaling(self, value):
        try:
            return original_reverse_widget_scaling(self, value)
        except ZeroDivisionError:
            setattr(self, "_CTkScalingBaseClass__widget_scaling", 1.0)
            return value

    def _safe_reverse_window_scaling(self, value):
        try:
            return original_reverse_window_scaling(self, value)
        except ZeroDivisionError:
            setattr(self, "_CTkScalingBaseClass__window_scaling", 1.0)
            return int(value)

    CTkScalingBaseClass._reverse_widget_scaling = _safe_reverse_widget_scaling
    CTkScalingBaseClass._reverse_window_scaling = _safe_reverse_window_scaling
    CTkScalingBaseClass._musuq_scaling_guard_installed = True


_install_customtkinter_scaling_guard()


class MusuqApp(ctk.CTk):
    """Aplicación principal"""
    
    def __init__(self):
        super().__init__()
        
        print("🚀 Iniciando MUSUQ Cloud Desktop...")
        
        # Cargar configuración
        Config.load()
        
        # Configurar tema
        ThemeManager.set_theme("dark")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Escala base segura para evitar estados transitorios de escala 0.
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)
        
        # Configurar ventana principal (oculta inicialmente)
        self.title(Config.APP_NAME)
        self.geometry(Config.MAIN_SIZE)
        self.minsize(*Config.MIN_SIZE)
        
        # Ocultar ventana principal hasta login exitoso
        self.withdraw()
        
        # Centrar ventana
        self.center_window()
        
        # Mostrar login
        self.show_login()
    
    def center_window(self):
        """Centrar ventana en pantalla"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
    
    def show_login(self):
        """Mostrar ventana de login"""
        LoginWindow(self, on_login_success=self.on_login_success)
    
    def on_login_success(self, auth_client, user_data):
        """Callback cuando el login es exitoso"""
        print(f"✅ Login exitoso: {user_data.get('username', 'Usuario')}")
        
        # Mostrar ventana principal
        self.deiconify()
        
        # Crear MainWindow
        MainWindow(self, auth_client, user_data)


def main():
    """Función principal"""
    print("=" * 50)
    print("  MUSUQ CLOUD - Sistema de Gestión Educativa")
    print("=" * 50)
    print(f"  Versión: {Config.APP_VERSION}")
    print(f"  Backend: {Config.API_BASE_URL}")
    print("=" * 50)
    
    try:
        app = MusuqApp()
        app.mainloop()
    except KeyboardInterrupt:
        print("\n👋 Aplicación cerrada por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
