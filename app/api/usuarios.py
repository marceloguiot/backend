# ==================== EMPIEZAN CAMBIOS ====================
# Archivo nuevo: CRUD completo de usuarios
# Creado para manejar todas las operaciones de usuarios
# ==================== EMPIEZAN CAMBIOS ====================

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime
import hashlib

from app.db.database import get_db

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])


# ==================== EMPIEZAN CAMBIOS ====================
# Modelos Pydantic para usuarios
# ==================== EMPIEZAN CAMBIOS ====================

class UsuarioCreate(BaseModel):
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    nombre_usuario: str
    correo: EmailStr
    password: str
    tipo_usuario: int
    clave_de_rumiantes: Optional[str] = None
    vigencia_inicio: date
    vigencia_fin: date
    activo: bool = True


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    nombre_usuario: Optional[str] = None
    correo: Optional[EmailStr] = None
    password: Optional[str] = None
    tipo_usuario: Optional[int] = None
    clave_de_rumiantes: Optional[str] = None
    vigencia_inicio: Optional[date] = None
    vigencia_fin: Optional[date] = None
    activo: Optional[bool] = None


def hash_password(password: str) -> str:
    """Hashea la contraseña usando SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Consultar usuarios con filtros
# ==================== EMPIEZAN CAMBIOS ====================

@router.get("")
def consultar_usuarios(
    nombre_usuario: Optional[str] = None,
    correo: Optional[str] = None,
    clave_de_rumiantes: Optional[str] = None,
    tipo_usuario: Optional[int] = None,
    activo: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Consulta usuarios con filtros opcionales
    """
    sql = """
        SELECT
            u.id_usuario,
            u.nombre,
            u.apellido_paterno,
            u.apellido_materno,
            u.nombre_usuario,
            u.correo,
            u.tipo_usuario,
            u.clave_de_rumiantes,
            u.vigencia_inicio,
            u.vigencia_fin,
            u.activo,
            u.fecha_creacion,
            t.nombre_tipo
        FROM usuarios u
        LEFT JOIN tipos_usuario t ON t.id_tipo = u.tipo_usuario
        WHERE 1=1
    """
    params = {"limit": int(limit)}

    if nombre_usuario:
        sql += " AND u.nombre_usuario LIKE :nombre_usuario"
        params["nombre_usuario"] = f"%{nombre_usuario.strip()}%"

    if correo:
        sql += " AND u.correo LIKE :correo"
        params["correo"] = f"%{correo.strip()}%"

    if clave_de_rumiantes:
        sql += " AND u.clave_de_rumiantes LIKE :clave_de_rumiantes"
        params["clave_de_rumiantes"] = f"%{clave_de_rumiantes.strip()}%"

    if tipo_usuario is not None:
        sql += " AND u.tipo_usuario = :tipo_usuario"
        params["tipo_usuario"] = int(tipo_usuario)

    if activo is not None:
        sql += " AND u.activo = :activo"
        params["activo"] = 1 if activo else 0

    sql += " ORDER BY u.id_usuario DESC LIMIT :limit"

    rows = db.execute(text(sql), params).mappings().all()

    # Formatear respuesta
    usuarios = []
    for row in rows:
        usuario = dict(row)
        usuario["nombre_completo"] = f"{usuario['nombre']} {usuario['apellido_paterno']} {usuario.get('apellido_materno', '')}".strip()
        usuarios.append(usuario)

    return usuarios


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Obtener usuario por ID
# ==================== EMPIEZAN CAMBIOS ====================

@router.get("/{id_usuario}")
def obtener_usuario(id_usuario: int, db: Session = Depends(get_db)):
    """
    Obtiene un usuario específico por ID
    """
    sql = text("""
        SELECT
            u.id_usuario,
            u.nombre,
            u.apellido_paterno,
            u.apellido_materno,
            u.nombre_usuario,
            u.correo,
            u.tipo_usuario,
            u.clave_de_rumiantes,
            u.vigencia_inicio,
            u.vigencia_fin,
            u.activo,
            u.fecha_creacion,
            t.nombre_tipo
        FROM usuarios u
        LEFT JOIN tipos_usuario t ON t.id_tipo = u.tipo_usuario
        WHERE u.id_usuario = :id_usuario
    """)

    row = db.execute(sql, {"id_usuario": id_usuario}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario = dict(row)
    usuario["nombre_completo"] = f"{usuario['nombre']} {usuario['apellido_paterno']} {usuario.get('apellido_materno', '')}".strip()

    return usuario


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Crear nuevo usuario
# ==================== EMPIEZAN CAMBIOS ====================

@router.post("")
def crear_usuario(payload: UsuarioCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo usuario en el sistema
    """
    try:
        # Validar que el nombre de usuario no exista
        check_sql = text("""
            SELECT id_usuario FROM usuarios
            WHERE nombre_usuario = :nombre_usuario
        """)
        existe = db.execute(check_sql, {"nombre_usuario": payload.nombre_usuario}).first()

        if existe:
            raise HTTPException(
                status_code=400,
                detail="El nombre de usuario ya existe"
            )

        # Validar que el correo no exista
        check_email_sql = text("""
            SELECT id_usuario FROM usuarios
            WHERE correo = :correo
        """)
        existe_email = db.execute(check_email_sql, {"correo": payload.correo}).first()

        if existe_email:
            raise HTTPException(
                status_code=400,
                detail="El correo electrónico ya está registrado"
            )

        # Hash de la contraseña
        password_hash = hash_password(payload.password)

        # Insertar usuario
        insert_sql = text("""
            INSERT INTO usuarios (
                nombre,
                apellido_paterno,
                apellido_materno,
                nombre_usuario,
                correo,
                password_hash,
                tipo_usuario,
                clave_de_rumiantes,
                vigencia_inicio,
                vigencia_fin,
                activo,
                fecha_creacion
            ) VALUES (
                :nombre,
                :apellido_paterno,
                :apellido_materno,
                :nombre_usuario,
                :correo,
                :password_hash,
                :tipo_usuario,
                :clave_de_rumiantes,
                :vigencia_inicio,
                :vigencia_fin,
                :activo,
                NOW()
            )
        """)

        db.execute(insert_sql, {
            "nombre": payload.nombre,
            "apellido_paterno": payload.apellido_paterno,
            "apellido_materno": payload.apellido_materno,
            "nombre_usuario": payload.nombre_usuario,
            "correo": payload.correo,
            "password_hash": password_hash,
            "tipo_usuario": payload.tipo_usuario,
            "clave_de_rumiantes": payload.clave_de_rumiantes,
            "vigencia_inicio": payload.vigencia_inicio,
            "vigencia_fin": payload.vigencia_fin,
            "activo": 1 if payload.activo else 0
        })

        # Obtener ID del usuario creado
        new_id = db.execute(text("SELECT LAST_INSERT_ID() AS id")).mappings().first()["id"]

        db.commit()

        return {
            "success": True,
            "message": "Usuario creado exitosamente",
            "id_usuario": int(new_id)
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear usuario: {str(e)}")


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Actualizar usuario
# ==================== EMPIEZAN CAMBIOS ====================

@router.put("/{id_usuario}")
def actualizar_usuario(id_usuario: int, payload: UsuarioUpdate, db: Session = Depends(get_db)):
    """
    Actualiza los datos de un usuario existente
    """
    try:
        # Verificar que el usuario existe
        check_sql = text("SELECT id_usuario FROM usuarios WHERE id_usuario = :id_usuario")
        existe = db.execute(check_sql, {"id_usuario": id_usuario}).first()

        if not existe:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Construir UPDATE dinámicamente
        campos = []
        params = {"id_usuario": id_usuario}

        if payload.nombre is not None:
            campos.append("nombre = :nombre")
            params["nombre"] = payload.nombre

        if payload.apellido_paterno is not None:
            campos.append("apellido_paterno = :apellido_paterno")
            params["apellido_paterno"] = payload.apellido_paterno

        if payload.apellido_materno is not None:
            campos.append("apellido_materno = :apellido_materno")
            params["apellido_materno"] = payload.apellido_materno

        if payload.nombre_usuario is not None:
            # Verificar que no exista otro usuario con ese nombre
            check_username = text("""
                SELECT id_usuario FROM usuarios
                WHERE nombre_usuario = :nombre_usuario AND id_usuario != :id_usuario
            """)
            existe_username = db.execute(check_username, {
                "nombre_usuario": payload.nombre_usuario,
                "id_usuario": id_usuario
            }).first()

            if existe_username:
                raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

            campos.append("nombre_usuario = :nombre_usuario")
            params["nombre_usuario"] = payload.nombre_usuario

        if payload.correo is not None:
            # Verificar que no exista otro usuario con ese correo
            check_email = text("""
                SELECT id_usuario FROM usuarios
                WHERE correo = :correo AND id_usuario != :id_usuario
            """)
            existe_email = db.execute(check_email, {
                "correo": payload.correo,
                "id_usuario": id_usuario
            }).first()

            if existe_email:
                raise HTTPException(status_code=400, detail="El correo ya está registrado")

            campos.append("correo = :correo")
            params["correo"] = payload.correo

        if payload.password is not None:
            campos.append("password_hash = :password_hash")
            params["password_hash"] = hash_password(payload.password)

        if payload.tipo_usuario is not None:
            campos.append("tipo_usuario = :tipo_usuario")
            params["tipo_usuario"] = payload.tipo_usuario

        if payload.clave_de_rumiantes is not None:
            campos.append("clave_de_rumiantes = :clave_de_rumiantes")
            params["clave_de_rumiantes"] = payload.clave_de_rumiantes

        if payload.vigencia_inicio is not None:
            campos.append("vigencia_inicio = :vigencia_inicio")
            params["vigencia_inicio"] = payload.vigencia_inicio

        if payload.vigencia_fin is not None:
            campos.append("vigencia_fin = :vigencia_fin")
            params["vigencia_fin"] = payload.vigencia_fin

        if payload.activo is not None:
            campos.append("activo = :activo")
            params["activo"] = 1 if payload.activo else 0

        if not campos:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        # Ejecutar UPDATE
        update_sql = f"""
            UPDATE usuarios
            SET {', '.join(campos)}
            WHERE id_usuario = :id_usuario
        """

        db.execute(text(update_sql), params)
        db.commit()

        return {
            "success": True,
            "message": "Usuario actualizado exitosamente"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar usuario: {str(e)}")


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Desactivar usuario (baja lógica)
# ==================== EMPIEZAN CAMBIOS ====================

@router.patch("/{id_usuario}/desactivar")
def desactivar_usuario(id_usuario: int, db: Session = Depends(get_db)):
    """
    Desactiva un usuario (baja lógica)
    """
    try:
        sql = text("""
            UPDATE usuarios
            SET activo = 0
            WHERE id_usuario = :id_usuario
        """)

        result = db.execute(sql, {"id_usuario": id_usuario})
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {
            "success": True,
            "message": "Usuario desactivado exitosamente"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al desactivar usuario: {str(e)}")


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Reactivar usuario
# ==================== EMPIEZAN CAMBIOS ====================

@router.patch("/{id_usuario}/reactivar")
def reactivar_usuario(id_usuario: int, db: Session = Depends(get_db)):
    """
    Reactiva un usuario previamente desactivado
    """
    try:
        sql = text("""
            UPDATE usuarios
            SET activo = 1
            WHERE id_usuario = :id_usuario
        """)

        result = db.execute(sql, {"id_usuario": id_usuario})
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {
            "success": True,
            "message": "Usuario reactivado exitosamente"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al reactivar usuario: {str(e)}")


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Eliminar usuario permanentemente
# ==================== EMPIEZAN CAMBIOS ====================

@router.delete("/{id_usuario}")
def eliminar_usuario(id_usuario: int, db: Session = Depends(get_db)):
    """
    Elimina permanentemente un usuario
    PRECAUCIÓN: Esta operación no se puede deshacer
    """
    try:
        sql = text("""
            DELETE FROM usuarios
            WHERE id_usuario = :id_usuario
        """)

        result = db.execute(sql, {"id_usuario": id_usuario})
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {
            "success": True,
            "message": "Usuario eliminado permanentemente"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar usuario: {str(e)}")

# ==================== TERMINAN CAMBIOS ====================
