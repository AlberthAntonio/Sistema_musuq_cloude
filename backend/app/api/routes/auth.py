"""
Rutas de autenticación - Login y verificación de token.
Usando capa de servicios.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.auth import Token, UsuarioResponse
from app.services.auth_service import auth_service

router = APIRouter()

# OAuth2 scheme para extraer token del header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Usuario:
    """
    Dependency para obtener el usuario actual desde el token JWT.
    Uso: current_user: Usuario = Depends(get_current_user)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    usuario = auth_service.obtener_usuario_desde_token(db, token)
    
    if usuario is None:
        raise credentials_exception
    
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )
    
    return usuario


def require_role(*roles: str):
    """
    Dependency factory para requerir roles específicos.
    Uso: dependencies=[Depends(require_role("admin", "secretaria"))]
    """
    def role_checker(current_user: Usuario = Depends(get_current_user)):
        if not auth_service.validar_rol(current_user, roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere rol: {', '.join(roles)}"
            )
        return current_user
    return role_checker


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Autenticar usuario y retornar token JWT.
    
    - **username**: nombre de usuario
    - **password**: contraseña
    """
    try:
        return auth_service.login(db, form_data.username, form_data.password)
    except ValueError as e:
        error_msg = str(e)
        if "desactivado" in error_msg:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_msg)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg,
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UsuarioResponse)
async def get_current_user_info(current_user: Usuario = Depends(get_current_user)):
    """Obtener información del usuario actual."""
    return current_user


@router.post("/verify")
async def verify_token_endpoint(current_user: Usuario = Depends(get_current_user)):
    """Verificar si el token es válido."""
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "rol": current_user.rol
    }
