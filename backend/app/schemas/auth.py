"""
Esquemas Pydantic para autenticación.
"""
from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """Respuesta de token JWT."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Datos contenidos en el token."""
    user_id: Optional[int] = None
    username: Optional[str] = None
    rol: Optional[str] = None


class LoginRequest(BaseModel):
    """Datos de login."""
    username: str
    password: str


class UsuarioBase(BaseModel):
    """Esquema base de usuario."""
    username: str
    email: Optional[str] = None
    nombre_completo: str
    rol: str = "consulta"


class UsuarioCreate(UsuarioBase):
    """Esquema para crear usuario."""
    password: str


class UsuarioResponse(UsuarioBase):
    """Esquema de respuesta de usuario."""
    id: int
    activo: bool
    
    class Config:
        from_attributes = True


class UsuarioUpdate(BaseModel):
    """Esquema para actualizar usuario."""
    email: Optional[str] = None
    nombre_completo: Optional[str] = None
    rol: Optional[str] = None
    activo: Optional[bool] = None
    password: Optional[str] = None
