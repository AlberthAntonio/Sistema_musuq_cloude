"""
Configuración central del cliente desktop
Sistema Musuq Cloud
"""

import json
from pathlib import Path
from typing import Optional


class Config:
    """Configuración global del sistema"""
    
    # ==================== BACKEND API ====================
    API_BASE_URL = "http://localhost:8000"
    API_TIMEOUT = 10  # segundos
    
    # ==================== APLICACIÓN ====================
    APP_NAME = "MUSUQ Cloud"
    APP_VERSION = "2.0.0"
    YEAR = 2026
    
    # ==================== VENTANAS ====================
    LOGIN_SIZE = "420x520"
    MAIN_SIZE = "1400x850"
    MIN_SIZE = (1000, 600)
    
    # ==================== DIRECTORIOS ====================
    BASE_DIR = Path(__file__).parent.parent
    CONFIG_FILE = BASE_DIR / "config.json"
    SESSION_FILE = BASE_DIR / "session.json"
    ASSETS_DIR = BASE_DIR / "assets"
    
    # ==================== CREDENCIALES ====================
    # Solo para desarrollo
    DEFAULT_USER = "admin"
    DEFAULT_PASS = "admin123"
    
    # ==================== MÉTODOS ====================
    
    @classmethod
    def load(cls) -> dict:
        """Cargar configuración desde archivo JSON"""
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cls.API_BASE_URL = data.get('api_url', cls.API_BASE_URL)
                    return data
            except Exception as e:
                print(f"Error cargando config: {e}")
        return {}
    
    @classmethod
    def save(cls, **kwargs):
        """Guardar configuración a archivo JSON"""
        try:
            data = cls.load()
            data.update(kwargs)
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error guardando config: {e}")
    
    @classmethod
    def get_api_url(cls, endpoint: str) -> str:
        """Obtener URL completa de un endpoint"""
        return f"{cls.API_BASE_URL}{endpoint}"
