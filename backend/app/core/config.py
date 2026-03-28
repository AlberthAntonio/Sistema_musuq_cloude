"""
Configuración central de la aplicación.
Lee variables de entorno y define settings globales.
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Configuración de la aplicación usando Pydantic Settings."""
    
    # Información de la app
    APP_NAME: str = "Sistema Musuq Cloud"
    DEBUG: bool = False  # False por defecto - se activa en .env de desarrollo
    
    # Base de datos
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/musuq_db"
    USE_SQLITE: bool = False
    SQLITE_URL: str = "sqlite:///./musuq_dev.db"
    
    # JWT - Access Token
    SECRET_KEY: str = "CAMBIAR-EN-PRODUCCION-usar-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hora en producción
    
    # JWT - Refresh Token
    REFRESH_SECRET_KEY: str = "REFRESH-SECRET-CAMBIAR-EN-PRODUCCION"
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS - en producción establecer IPs específicas del cliente desktop
    # Ejemplo: "http://192.168.1.10,http://192.168.1.20"
    ALLOWED_ORIGINS: str = "*"
    
    # Servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "json"  # json | pretty (pretty para desarrollo)
    
    # Rate limiting (intentos de login por IP por minuto)
    LOGIN_RATE_LIMIT: int = 10
    
    @property
    def db_url(self) -> str:
        """Retorna la URL de BD según configuración."""
        if self.USE_SQLITE:
            return self.SQLITE_URL
        return self.DATABASE_URL
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Retorna lista de origins permitidos para CORS."""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
    
    class Config:
        env_file = ".env"
        extra = "ignore"


# Instancia global de configuración
settings = Settings()
