"""
Modelo de Usuario para autenticación y autorización.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from app.db.database import Base


class Usuario(Base):
    """Modelo de usuario del sistema."""
    
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    nombre_completo = Column(String(150), nullable=False)
    
    # Roles: admin, secretaria, docente, consulta
    rol = Column(String(20), default="consulta")
    
    # Estado
    activo = Column(Boolean, default=True)
    
    # Timestamps
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    ultimo_acceso = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Usuario {self.username} ({self.rol})>"
