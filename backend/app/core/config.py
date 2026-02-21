"""
Configuración central de la aplicación.
Lee variables de entorno y define settings globales.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Configuración de la aplicación usando Pydantic Settings."""
    
    # Información de la app
    APP_NAME: str = "Sistema Musuq Cloud"
    DEBUG: bool = True
    
    # Base de datos
    # Para desarrollo local usamos PostgreSQL
    # Formato: postgresql://usuario:password@host:puerto/nombre_bd
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/musuq_db"
    
    # Opción SQLite para desarrollo sin PostgreSQL
    USE_SQLITE: bool = False
    SQLITE_URL: str = "sqlite:///./musuq_dev.db"
    
    # JWT Configuration
    SECRET_KEY: str = "tu-clave-secreta-cambiar-en-produccion-123456789"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas
    
    # Servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    @property
    def db_url(self) -> str:
        """Retorna la URL de BD según configuración."""
        if self.USE_SQLITE:
            return self.SQLITE_URL
        return self.DATABASE_URL
    
    class Config:
        env_file = ".env"
        extra = "ignore"


# Instancia global de configuración
settings = Settings()
