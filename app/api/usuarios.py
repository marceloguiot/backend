from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime
import hashlib

from app.db.database import get_db

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])

class UsuarioCreate(BaseModel):
    nombre: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    nombre_usuario: str
    email: Optional[str] = None
    password: str
    tipo_usuario: int
    clave_de_rumiantes: Optional[str] = None
    vigencia_inicio: Optional[str] = None
    vigencia_fin: Optional[str] = None
    activo: bool = True


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    nombre_usuario: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    tipo_usuario: Optional[int] = None
    clave_de_rumiantes: Optional[str] = None
    vigencia_inicio: Optional[str] = None
    vigencia_fin: Optional[str] = None
    activo: Optional[bool] = None


def hash_password(password: str) -> str:
    """Hashea la contraseña usando SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


@router.get("")
def consultar_usuarios(
    nombre_usuario: Optional[str] = None,
    clave_de_rumiantes: Optional[str] = None,
    email: Optional[str] = None,
    nombre: Optional[str] = None,
    activo: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Consulta usuarios con filtros opcionales
    """
    # BD: id_usuario, id_rol, nombre, usuario, password_hash, email, telefono, activo, fecha_creacion, fecha_actualizacion
    sql = """
        SELECT
            u.id_usuario,
            u.usuario,
            u.nombre,
            u.id_rol,
            u.activo,
            u.email,
            u.telefono,
            u.fecha_creacion,
            r.nombre as rol_nombre,
            r.descripcion as rol_descripcion
        FROM usuarios u
        INNER JOIN cat_rol r ON r.id_rol = u.id_rol
        WHERE 1=1
    """
    params = {"limit": int(limit)}

    # Mapear nombre_usuario del frontend a usuario de la BD
    if nombre_usuario:
        sql += " AND u.usuario LIKE :usuario"
        params["usuario"] = f"%{nombre_usuario.strip()}%"

    if nombre:
        sql += " AND u.nombre LIKE :nombre"
        params["nombre"] = f"%{nombre.strip()}%"

    # Nota: clave_de_rumiantes y correo no existen en BD real, se ignoran
    # if clave_de_rumiantes:
    #     pass  # Campo no existe en BD
    # if correo:
    #     pass  # Campo no existe en BD

    if activo is not None:
        sql += " AND u.activo = :activo"
        params["activo"] = 1 if activo else 0

    sql += " ORDER BY u.id_usuario DESC LIMIT :limit"

    rows = db.execute(text(sql), params).mappings().all()

    # Formatear respuesta mapeando campos reales de DB a campos esperados por frontend
    usuarios = []
    for row in rows:
        usuario_data = {
            "id_usuario": row["id_usuario"],
            "nombre": row["nombre"],
            "apellido_paterno": "",  # No existe en BD real
            "apellido_materno": "",  # No existe en BD real
            "nombre_completo": row["nombre"],
            "nombre_usuario": row["usuario"],  # Mapear usuario -> nombre_usuario
            "email": row["email"],
            "telefono": row["telefono"],
            "tipo_usuario": row["id_rol"],  # Mapear id_rol -> tipo_usuario
            "clave_de_rumiantes": "",  # No existe en BD real
            "vigencia_inicio": "",  # No existe en BD real
            "vigencia_fin": "",  # No existe en BD real
            "activo": bool(row["activo"]),
            "fecha_creacion": row["fecha_creacion"],
            "rol_nombre": row["rol_nombre"],
            "rol_descripcion": row["rol_descripcion"]
        }
        usuarios.append(usuario_data)

    return usuarios


@router.get("/{id_usuario}")
def obtener_usuario(id_usuario: int, db: Session = Depends(get_db)):
    """
    Obtiene un usuario específico por ID
    """
    sql = text("""
        SELECT
            u.id_usuario,
            u.usuario,
            u.nombre,
            u.id_rol,
            u.activo,
            u.email,
            u.telefono,
            u.fecha_creacion,
            r.nombre as rol_nombre,
            r.descripcion as rol_descripcion
        FROM usuarios u
        INNER JOIN cat_rol r ON r.id_rol = u.id_rol
        WHERE u.id_usuario = :id_usuario
    """)

    row = db.execute(sql, {"id_usuario": id_usuario}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Mapear campos reales de DB a campos esperados por frontend
    usuario_data = {
        "id_usuario": row["id_usuario"],
        "nombre": row["nombre"],
        "apellido_paterno": "",
        "apellido_materno": "",
        "nombre_completo": row["nombre"],
        "nombre_usuario": row["usuario"],
        "email": row["email"],
        "telefono": row["telefono"],
        "tipo_usuario": row["id_rol"],
        "clave_de_rumiantes": "",
        "vigencia_inicio": "",
        "vigencia_fin": "",
        "activo": bool(row["activo"]),
        "fecha_creacion": row["fecha_creacion"],
        "rol_nombre": row["rol_nombre"],
        "rol_descripcion": row["rol_descripcion"]
    }

    return usuario_data


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Crear nuevo usuario
# ==================== EMPIEZAN CAMBIOS ====================

@router.post("")
def crear_usuario(payload: UsuarioCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo usuario en el sistema
    Mapea campos del frontend (estructura antigua) a campos reales de BD
    """
    try:
        # Validar que el nombre de usuario no exista
        check_sql = text("""
            SELECT id_usuario FROM usuarios
            WHERE usuario = :usuario
        """)
        existe = db.execute(check_sql, {"usuario": payload.nombre_usuario}).first()

        if existe:
            raise HTTPException(
                status_code=400,
                detail="El nombre de usuario ya existe"
            )

        # Validar que el id_rol exista en cat_rol (tipo_usuario del frontend)
        check_rol_sql = text("""
            SELECT id_rol FROM cat_rol
            WHERE id_rol = :id_rol
        """)
        existe_rol = db.execute(check_rol_sql, {"id_rol": payload.tipo_usuario}).first()

        if not existe_rol:
            raise HTTPException(
                status_code=400,
                detail="El rol especificado no existe"
            )

        # Hash de la contraseña
        password_hash = hash_password(payload.password)

        # Construir nombre completo a partir de los campos del frontend
        nombre_completo = f"{payload.nombre} {payload.apellido_paterno or ''} {payload.apellido_materno or ''}".strip()

        # Insertar usuario usando solo los campos que existen en la BD real
        # BD: id_usuario, id_rol, nombre, usuario, password_hash, email, telefono, activo, fecha_creacion, fecha_actualizacion
        insert_sql = text("""
            INSERT INTO usuarios (
                usuario,
                password_hash,
                nombre,
                id_rol,
                email,
                activo,
                fecha_creacion
            ) VALUES (
                :usuario,
                :password_hash,
                :nombre,
                :id_rol,
                :email,
                :activo,
                NOW()
            )
        """)

        db.execute(insert_sql, {
            "usuario": payload.nombre_usuario,
            "password_hash": password_hash,
            "nombre": nombre_completo,
            "id_rol": payload.tipo_usuario,
            "email": payload.email or "",
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
    Mapea campos del frontend (estructura antigua) a campos reales de BD
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

        # Mapear nombre_usuario del frontend a usuario de la BD
        if payload.nombre_usuario is not None:
            # Verificar que no exista otro usuario con ese nombre
            check_username = text("""
                SELECT id_usuario FROM usuarios
                WHERE usuario = :usuario AND id_usuario != :id_usuario
            """)
            existe_username = db.execute(check_username, {
                "usuario": payload.nombre_usuario,
                "id_usuario": id_usuario
            }).first()

            if existe_username:
                raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

            campos.append("usuario = :usuario")
            params["usuario"] = payload.nombre_usuario

        # Si hay cambios en nombre, apellido_paterno o apellido_materno, actualizar campo nombre
        if payload.nombre is not None or payload.apellido_paterno is not None or payload.apellido_materno is not None:
            # Obtener valores actuales si no vienen en el payload
            if payload.nombre is None or payload.apellido_paterno is None:
                current_sql = text("SELECT nombre FROM usuarios WHERE id_usuario = :id_usuario")
                current = db.execute(current_sql, {"id_usuario": id_usuario}).first()
                # Asumimos que el nombre actual podría tener el formato "Nombre Apellido"
                # pero solo usamos lo que viene en el payload

            nombre_completo = f"{payload.nombre or ''} {payload.apellido_paterno or ''} {payload.apellido_materno or ''}".strip()
            if nombre_completo:
                campos.append("nombre = :nombre")
                params["nombre"] = nombre_completo

        if payload.password is not None:
            campos.append("password_hash = :password_hash")
            params["password_hash"] = hash_password(payload.password)

        # Mapear tipo_usuario del frontend a id_rol de la BD
        if payload.tipo_usuario is not None:
            # Validar que el id_rol exista en cat_rol
            check_rol_sql = text("""
                SELECT id_rol FROM cat_rol
                WHERE id_rol = :id_rol
            """)
            existe_rol = db.execute(check_rol_sql, {"id_rol": payload.tipo_usuario}).first()

            if not existe_rol:
                raise HTTPException(status_code=400, detail="El rol especificado no existe")

            campos.append("id_rol = :id_rol")
            params["id_rol"] = payload.tipo_usuario

        if payload.activo is not None:
            campos.append("activo = :activo")
            params["activo"] = 1 if payload.activo else 0

        # Email sí existe en la BD
        if payload.email is not None:
            campos.append("email = :email")
            params["email"] = payload.email

        # Nota: clave_de_rumiantes, vigencia_inicio, vigencia_fin no existen en BD real
        # por lo que se ignoran

        if not campos:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        # Agregar fecha_actualizacion
        campos.append("fecha_actualizacion = NOW()")

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
