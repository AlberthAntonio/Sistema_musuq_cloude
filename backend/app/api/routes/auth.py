"""
Rutas de autenticación - Login, Refresh Token y verificación.
Incluye rate limiting simple por IP + RBAC dependencies.
"""
import time
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from pydantic import BaseModel, Field
from app.db import get_db
from app.models.usuario import Usuario
from app.schemas.auth import TokenPair, Token, RefreshRequest, UsuarioResponse
from app.services.auth_service import auth_service
from app.services.usuario_service import usuario_service
from app.core.config import settings


class CambiarPasswordRequest(BaseModel):
    """Payload para cambiar la contraseña del usuario autenticado."""
    password_actual: str = Field(..., min_length=1, description="Contraseña actual")
    password_nueva: str = Field(..., min_length=6, description="Nueva contraseña (mín. 6 caracteres)")

router = APIRouter()

# OAuth2 scheme para extraer token del header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ---------------------------------------------------------------------------
# Rate limiter simple en memoria (ventana deslizante por IP)
# En producción con múltiples workers usar Redis.
# ---------------------------------------------------------------------------
_login_attempts: dict = defaultdict(list)  # {ip: [timestamp, ...]}
_RATE_WINDOW = 60  # segundos


def _check_rate_limit(ip: str) -> None:
    """Lanza 429 si la IP superó LOGIN_RATE_LIMIT intentos en la última ventana."""
    now = time.time()
    attempts = [t for t in _login_attempts[ip] if now - t < _RATE_WINDOW]
    _login_attempts[ip] = attempts
    if len(attempts) >= settings.LOGIN_RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos de login. Intenta en {_RATE_WINDOW} segundos."
        )
    _login_attempts[ip].append(now)


# ---------------------------------------------------------------------------
# Dependencies de autenticación
# ---------------------------------------------------------------------------

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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario desactivado")
    
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


def verificar_no_auxiliar(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """
    Dependency que bloquea a usuarios con rol AUXILIAR en operaciones de escritura.
    """
    if current_user.rol and current_user.rol.upper() == "AUXILIAR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )
    return current_user


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenPair)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Autenticar usuario y retornar par de tokens (access + refresh).
    
    - **username**: nombre de usuario
    - **password**: contraseña
    """
    # Rate limiting por IP
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)
    
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


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(
    body: RefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Renovar el par de tokens usando un refresh token válido.
    El cliente desktop debe llamar a este endpoint cuando el access token expire.
    """
    try:
        return auth_service.refresh(db, body.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UsuarioResponse)
async def get_current_user_info(current_user: Usuario = Depends(get_current_user)):
    """Obtener información del usuario actual."""
    return current_user


@router.post("/cambiar-password", status_code=status.HTTP_204_NO_CONTENT)
async def cambiar_password(
    body: CambiarPasswordRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Cambiar la contraseña del usuario autenticado.
    Requiere la contraseña actual para verificación.
    """
    # Verificar contraseña actual
    usuario_verificado = auth_service.validar_credenciales(db, current_user.username, body.password_actual)
    if not usuario_verificado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta",
        )
    usuario_service.cambiar_password(db, current_user.id, body.password_nueva)


@router.post("/verify")
async def verify_token_endpoint(current_user: Usuario = Depends(get_current_user)):
    """Verificar si el token es válido."""
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "rol": current_user.rol
    }
