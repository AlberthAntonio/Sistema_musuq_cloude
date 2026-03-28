"""
Servicio de Autenticación - Lógica de login, tokens y verificación.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.core.security import (
    verify_password, create_access_token, create_refresh_token,
    verify_token, verify_refresh_token
)


class AuthService:
    """Servicio para operaciones de autenticación."""
    
    # ==================== VALIDACIONES ====================
    
    def validar_credenciales(self, db: Session, username: str, password: str) -> Optional[Usuario]:
        """Valida credenciales y retorna el usuario si son correctas."""
        user = db.query(Usuario).filter(Usuario.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def validar_usuario_activo(self, usuario: Usuario) -> bool:
        """Verifica si el usuario está activo."""
        return usuario.activo
    
    def validar_rol(self, usuario: Usuario, roles_permitidos: tuple) -> bool:
        """Verifica si el usuario tiene uno de los roles permitidos."""
        return usuario.rol in roles_permitidos
    
    # ==================== OPERACIONES ====================
    
    def login(self, db: Session, username: str, password: str) -> Dict[str, Any]:
        """
        Autenticar usuario y retornar par de tokens (access + refresh).
        Returns: {"access_token": str, "refresh_token": str, "token_type": "bearer"}
        Raises: ValueError si credenciales inválidas o usuario inactivo
        """
        usuario = self.validar_credenciales(db, username, password)
        if not usuario:
            raise ValueError("Usuario o contraseña incorrectos")
        
        if not self.validar_usuario_activo(usuario):
            raise ValueError("Usuario desactivado")
        
        # Actualizar último acceso
        usuario.ultimo_acceso = datetime.utcnow()
        db.commit()
        
        token_data = {"sub": str(usuario.id), "username": usuario.username, "rol": usuario.rol}
        
        return {
            "access_token": create_access_token(data=token_data),
            "refresh_token": create_refresh_token(data={"sub": str(usuario.id)}),
            "token_type": "bearer"
        }
    
    def refresh(self, db: Session, refresh_token: str) -> Dict[str, Any]:
        """
        Genera un nuevo par de tokens a partir de un refresh token válido.
        Returns: {"access_token": str, "refresh_token": str, "token_type": "bearer"}
        Raises: ValueError si el refresh token es inválido o el usuario está inactivo
        """
        payload = verify_refresh_token(refresh_token)
        if payload is None:
            raise ValueError("Refresh token inválido o expirado")
        
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise ValueError("Refresh token inválido")
        
        usuario = db.query(Usuario).filter(Usuario.id == int(user_id_str)).first()
        if not usuario:
            raise ValueError("Usuario no encontrado")
        if not usuario.activo:
            raise ValueError("Usuario desactivado")
        
        token_data = {"sub": str(usuario.id), "username": usuario.username, "rol": usuario.rol}
        
        return {
            "access_token": create_access_token(data=token_data),
            "refresh_token": create_refresh_token(data={"sub": str(usuario.id)}),
            "token_type": "bearer"
        }
    
    def obtener_usuario_desde_token(self, db: Session, token: str) -> Optional[Usuario]:
        """
        Decodifica el access token y retorna el usuario.
        Returns: Usuario o None si token inválido
        """
        payload = verify_token(token)
        if payload is None:
            return None
        
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None
        
        return db.query(Usuario).filter(Usuario.id == int(user_id_str)).first()
    
    def verificar_token(self, db: Session, token: str) -> Dict[str, Any]:
        """
        Verificar si un access token es válido.
        Returns: {"valid": bool, "user_id": int, "username": str, "rol": str}
        Raises: ValueError si token inválido
        """
        usuario = self.obtener_usuario_desde_token(db, token)
        if not usuario:
            raise ValueError("Token inválido")
        if not self.validar_usuario_activo(usuario):
            raise ValueError("Usuario desactivado")
        
        return {
            "valid": True,
            "user_id": usuario.id,
            "username": usuario.username,
            "rol": usuario.rol
        }


# Instancia global del servicio
auth_service = AuthService()
