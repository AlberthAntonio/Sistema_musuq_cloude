"""
Gestor de autenticación y sesiones
Sistema Musuq Cloud
"""

import json
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from .config import Config


class AuthManager:
    """Gestiona la sesión del usuario y tokens JWT"""
    
    def __init__(self):
        self.token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_data: Optional[Dict] = None
        self.login_time: Optional[datetime] = None
    
    def save_session(self, token: str, user_data: Dict, remember: bool = False,
                     refresh_token: Optional[str] = None):
        """Guardar sesión actual — persiste access + refresh token"""
        self.token = token
        self.refresh_token = refresh_token
        self.user_data = user_data
        self.login_time = datetime.now()
        
        if remember:
            try:
                session_data = {
                    "token": token,
                    "refresh_token": refresh_token,
                    "user_data": user_data,
                    "saved_at": self.login_time.isoformat()
                }
                with open(Config.SESSION_FILE, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=4)
            except Exception as e:
                print(f"Error guardando sesión: {e}")
    
    def load_session(self) -> bool:
        """Cargar sesión guardada si existe"""
        if not Config.SESSION_FILE.exists():
            return False
        
        try:
            with open(Config.SESSION_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.token = data.get("token")
                self.refresh_token = data.get("refresh_token")
                self.user_data = data.get("user_data")
                return True
        except Exception as e:
            print(f"Error cargando sesión: {e}")
            return False
    
    def clear_session(self):
        """Cerrar sesión y limpiar datos"""
        self.token = None
        self.refresh_token = None
        self.user_data = None
        self.login_time = None
        
        # Eliminar archivo de sesión
        try:
            if Config.SESSION_FILE.exists():
                Config.SESSION_FILE.unlink()
        except Exception as e:
            print(f"Error eliminando sesión: {e}")
    
    def is_authenticated(self) -> bool:
        """Verificar si hay sesión activa"""
        return self.token is not None
    
    def get_user_display_name(self) -> str:
        """Obtener nombre para mostrar"""
        if self.user_data:
            return self.user_data.get("nombre_completo", 
                   self.user_data.get("username", "Usuario"))
        return "Usuario"
    
    def get_user_role(self) -> str:
        """Obtener rol del usuario"""
        if self.user_data:
            return self.user_data.get("rol", "Usuario")
        return "Usuario"
