"""
Servicio de Usuarios - Lógica de negocio y validaciones.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.schemas.auth import UsuarioCreate, UsuarioUpdate
from app.core.security import get_password_hash


class UsuarioService:
    """Servicio para operaciones de usuarios."""
    
    # ==================== VALIDACIONES ====================
    
    def validar_username_unico(self, db: Session, username: str, usuario_id: Optional[int] = None) -> bool:
        """Verifica si el username ya existe. Retorna True si está disponible."""
        query = db.query(Usuario).filter(Usuario.username == username)
        if usuario_id:
            query = query.filter(Usuario.id != usuario_id)
        return query.first() is None
    
    def validar_email_unico(self, db: Session, email: str, usuario_id: Optional[int] = None) -> bool:
        """Verifica si el email ya existe. Retorna True si está disponible."""
        if not email:
            return True  # Email es opcional
        query = db.query(Usuario).filter(Usuario.email == email)
        if usuario_id:
            query = query.filter(Usuario.id != usuario_id)
        return query.first() is None
    
    def validar_puede_eliminar(self, usuario_id: int, current_user_id: int) -> bool:
        """Verifica si se puede eliminar el usuario."""
        return usuario_id != current_user_id  # No puede eliminar su propio usuario
    
    # ==================== OPERACIONES CRUD ====================
    
    def listar(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        activo: Optional[bool] = None
    ) -> List[Usuario]:
        """Listar usuarios con filtros opcionales."""
        query = db.query(Usuario)
        if activo is not None:
            query = query.filter(Usuario.activo == activo)
        return query.order_by(Usuario.username).offset(skip).limit(limit).all()
    
    def crear(self, db: Session, datos: UsuarioCreate) -> Usuario:
        """Crear nuevo usuario."""
        # Validar username único
        if not self.validar_username_unico(db, datos.username):
            raise ValueError("El nombre de usuario ya existe")
        
        # Validar email único
        if datos.email and not self.validar_email_unico(db, datos.email):
            raise ValueError("El email ya está registrado")
        
        usuario = Usuario(
            username=datos.username,
            email=datos.email,
            nombre_completo=datos.nombre_completo,
            rol=datos.rol,
            hashed_password=get_password_hash(datos.password)
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return usuario
    
    def obtener_por_id(self, db: Session, usuario_id: int) -> Optional[Usuario]:
        """Obtener usuario por ID."""
        return db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    def obtener_por_username(self, db: Session, username: str) -> Optional[Usuario]:
        """Obtener usuario por username."""
        return db.query(Usuario).filter(Usuario.username == username).first()
    
    def actualizar(self, db: Session, usuario_id: int, datos: UsuarioUpdate) -> Usuario:
        """Actualizar usuario."""
        usuario = self.obtener_por_id(db, usuario_id)
        if not usuario:
            raise ValueError("Usuario no encontrado")
        
        update_data = datos.model_dump(exclude_unset=True)
        
        # Hashear password si se proporciona
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        # Validar username único si se cambia
        if "username" in update_data and update_data["username"] != usuario.username:
            if not self.validar_username_unico(db, update_data["username"], usuario_id):
                raise ValueError("El nombre de usuario ya existe")
        
        for field, value in update_data.items():
            setattr(usuario, field, value)
        
        db.commit()
        db.refresh(usuario)
        return usuario
    
    def eliminar(self, db: Session, usuario_id: int, current_user_id: int) -> bool:
        """Eliminar usuario."""
        usuario = self.obtener_por_id(db, usuario_id)
        if not usuario:
            raise ValueError("Usuario no encontrado")
        
        if not self.validar_puede_eliminar(usuario_id, current_user_id):
            raise ValueError("No puedes eliminar tu propio usuario")
        
        db.delete(usuario)
        db.commit()
        return True
    
    def desactivar(self, db: Session, usuario_id: int) -> Usuario:
        """Desactivar usuario (soft delete)."""
        usuario = self.obtener_por_id(db, usuario_id)
        if not usuario:
            raise ValueError("Usuario no encontrado")
        
        usuario.activo = False
        db.commit()
        db.refresh(usuario)
        return usuario
    
    def cambiar_password(self, db: Session, usuario_id: int, nueva_password: str) -> Usuario:
        """Cambiar contraseña de usuario."""
        usuario = self.obtener_por_id(db, usuario_id)
        if not usuario:
            raise ValueError("Usuario no encontrado")
        
        usuario.hashed_password = get_password_hash(nueva_password)
        db.commit()
        db.refresh(usuario)
        return usuario


# Instancia global del servicio
usuario_service = UsuarioService()
