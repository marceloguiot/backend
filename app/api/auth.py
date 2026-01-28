# ==================== EMPIEZAN CAMBIOS ====================
# Archivo nuevo: Endpoints de autenticación
# Creado para manejar login, logout y validación de sesiones
# ==================== EMPIEZAN CAMBIOS ====================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import hashlib
import secrets

from app.db.database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ==================== EMPIEZAN CAMBIOS ====================
# Modelos Pydantic para login
# ==================== EMPIEZAN CAMBIOS ====================

class LoginRequest(BaseModel):
    nombre_usuario: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    usuario: Optional[dict] = None
    token: Optional[str] = None


# ==================== EMPIEZAN CAMBIOS ====================
# Función auxiliar para hashear contraseñas (SHA256)
# ==================== EMPIEZAN CAMBIOS ====================

def hash_password(password: str) -> str:
    """Hashea la contraseña usando SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def generar_token() -> str:
    """Genera un token de sesión aleatorio"""
    return secrets.token_urlsafe(32)


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint de login
# ==================== EMPIEZAN CAMBIOS ====================

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Endpoint de autenticación de usuarios
    - Valida usuario y contraseña
    - Retorna datos del usuario y token de sesión
    """
    try:
        usuario = payload.nombre_usuario.strip()
        password = payload.password

        if not usuario or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario y contraseña son requeridos"
            )

        # Hash de la contraseña ingresada
        password_hash = hash_password(password)

        # Buscar usuario en la base de datos con JOIN a cat_rol
        sql = text("""
            SELECT
                u.id_usuario,
                u.usuario,
                u.nombre,
                u.id_rol,
                u.activo,
                r.nombre as rol_nombre,
                r.descripcion as rol_descripcion
            FROM usuarios u
            INNER JOIN cat_rol r ON r.id_rol = u.id_rol
            WHERE u.usuario = :usuario
            AND u.password_hash = :password_hash
            LIMIT 1
        """)

        result = db.execute(sql, {
            "usuario": usuario,
            "password_hash": password_hash
        }).mappings().first()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos"
            )

        usuario_data = dict(result)

        # Validar que el usuario esté activo
        if not usuario_data.get("activo"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El usuario está inactivo"
            )

        # Generar token de sesión
        token = generar_token()

        # Obtener rol del usuario
        rol = usuario_data.get("rol_nombre", "")

        # Preparar respuesta
        usuario_response = {
            "id_usuario": usuario_data["id_usuario"],
            "nombre": usuario_data["nombre"],
            "nombre_completo": usuario_data["nombre"],
            "nombre_usuario": usuario_data["usuario"],
            "id_rol": usuario_data["id_rol"],
            "rol": rol,
            "rol_descripcion": usuario_data.get("rol_descripcion", "")
        }

        return LoginResponse(
            success=True,
            message="Login exitoso",
            usuario=usuario_response,
            token=token
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el servidor: {str(e)}"
        )


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint de logout
# ==================== EMPIEZAN CAMBIOS ====================

@router.post("/logout")
def logout():
    """
    Endpoint de cierre de sesión
    En una implementación con tokens, aquí se invalidaría el token
    """
    return {
        "success": True,
        "message": "Sesión cerrada exitosamente"
    }


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint para validar token/sesión
# ==================== EMPIEZAN CAMBIOS ====================

@router.get("/validate")
def validate_session(token: str):
    """
    Endpoint para validar si un token de sesión es válido
    Placeholder para implementación futura con base de datos de sesiones
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no proporcionado"
        )

    return {
        "valid": True,
        "message": "Token válido"
    }

# ==================== TERMINAN CAMBIOS ====================
