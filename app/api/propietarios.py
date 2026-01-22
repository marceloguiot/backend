# ==================== EMPIEZAN CAMBIOS ====================
# Se agregaron imports para Query y modelos Pydantic
# ==================== EMPIEZAN CAMBIOS ====================
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.db.database import get_db

router = APIRouter(prefix="/api/propietarios", tags=["propietarios"])


# ==================== EMPIEZAN CAMBIOS ====================
# Modelos Pydantic para propietarios
# ==================== EMPIEZAN CAMBIOS ====================

class PropietarioCreate(BaseModel):
    # BD: id_propietario, nombre, curp, rfc, telefono, email, estatus (ENUM: ACTIVO/FINADO), fecha_registro, fecha_actualizacion
    nombre: str
    curp: Optional[str] = None
    rfc: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    estatus: str = "ACTIVO"  # ACTIVO o FINADO

    # Campos del frontend que no existen en BD (se ignoran o mapean)
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    correo: Optional[EmailStr] = None  # Alias para email
    activo: Optional[bool] = None  # Mapea a estatus


class PropietarioUpdate(BaseModel):
    # BD: id_propietario, nombre, curp, rfc, telefono, email, estatus (ENUM: ACTIVO/FINADO), fecha_registro, fecha_actualizacion
    nombre: Optional[str] = None
    curp: Optional[str] = None
    rfc: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    estatus: Optional[str] = None

    # Campos del frontend que no existen en BD (se ignoran o mapean)
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    correo: Optional[EmailStr] = None  # Alias para email
    activo: Optional[bool] = None  # Mapea a estatus

# ==================== TERMINAN CAMBIOS ====================


# ==================== ENDPOINT ORIGINAL (sin cambios) ====================
@router.get("/por-curp")
def propietario_por_curp(curp: str, db: Session = Depends(get_db)):
    curp = (curp or "").strip().upper()
    if not curp:
        raise HTTPException(status_code=400, detail="CURP requerida")

    # BD: id_propietario, nombre, curp, rfc, telefono, email, estatus (ENUM: ACTIVO/FINADO), fecha_registro, fecha_actualizacion
    q = text("""
        SELECT
            id_propietario,
            nombre,
            curp,
            rfc,
            telefono,
            email,
            estatus,
            fecha_registro
        FROM propietarios
        WHERE curp = :curp
        LIMIT 1
    """)
    row = db.execute(q, {"curp": curp}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Propietario no encontrado")

    # Mapear campos reales a campos esperados por frontend
    propietario_data = {
        "id_propietario": row["id_propietario"],
        "nombre": row["nombre"],
        "apellido_paterno": "",  # No existe en BD real
        "apellido_materno": "",  # No existe en BD real
        "nombre_completo": row["nombre"],
        "curp": row["curp"],
        "rfc": row["rfc"],
        "telefono": row["telefono"],
        "email": row["email"],
        "correo": row["email"],  # Alias para frontend
        "estatus": row["estatus"],
        "activo": row["estatus"] == "ACTIVO",  # Mapear estatus -> activo
        "fecha_registro": row["fecha_registro"]
    }

    return propietario_data


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Consultar propietarios con múltiples filtros
# ==================== EMPIEZAN CAMBIOS ====================

@router.get("")
def consultar_propietarios(
    curp: Optional[str] = None,
    nombre: Optional[str] = None,
    upp: Optional[str] = None,
    estatus: Optional[str] = None,
    # Parámetros del frontend que no existen en BD (se ignoran)
    municipio: Optional[str] = None,
    localidad: Optional[str] = None,
    activo: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Consulta propietarios con filtros opcionales
    BD: id_propietario, nombre, curp, rfc, telefono, email, estatus (ENUM: ACTIVO/FINADO), fecha_registro, fecha_actualizacion
    """
    sql = """
        SELECT DISTINCT
            p.id_propietario,
            p.nombre,
            p.curp,
            p.rfc,
            p.telefono,
            p.email,
            p.estatus,
            p.fecha_registro
        FROM propietarios p
        LEFT JOIN upp u ON u.id_propietario = p.id_propietario
        WHERE 1=1
    """
    params = {"limit": int(limit)}

    if curp:
        sql += " AND p.curp LIKE :curp"
        params["curp"] = f"%{curp.strip().upper()}%"

    if nombre:
        sql += " AND p.nombre LIKE :nombre"
        params["nombre"] = f"%{nombre.strip()}%"

    if upp:
        sql += " AND u.clave_upp LIKE :upp"
        params["upp"] = f"%{upp.strip()}%"

    if estatus:
        sql += " AND p.estatus = :estatus"
        params["estatus"] = estatus.strip().upper()

    # Mapear activo (del frontend) a estatus (de la BD)
    if activo is not None:
        sql += " AND p.estatus = :estatus"
        params["estatus"] = "ACTIVO" if activo else "FINADO"

    # municipio y localidad no existen en la tabla propietarios real, se ignoran

    sql += " ORDER BY p.id_propietario DESC LIMIT :limit"

    rows = db.execute(text(sql), params).mappings().all()

    # Mapear campos reales de BD a campos esperados por frontend
    propietarios = []
    for row in rows:
        propietario_data = {
            "id_propietario": row["id_propietario"],
            "nombre": row["nombre"],
            "apellido_paterno": "",  # No existe en BD real
            "apellido_materno": "",  # No existe en BD real
            "nombre_completo": row["nombre"],
            "curp": row["curp"],
            "rfc": row["rfc"],
            "telefono": row["telefono"],
            "email": row["email"],
            "correo": row["email"],  # Alias para frontend
            "estatus": row["estatus"],
            "activo": row["estatus"] == "ACTIVO",  # Mapear estatus -> activo
            "fecha_registro": row["fecha_registro"]
        }
        propietarios.append(propietario_data)

    return propietarios


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Obtener propietario por ID
# ==================== EMPIEZAN CAMBIOS ====================

@router.get("/{id_propietario}")
def obtener_propietario(id_propietario: int, db: Session = Depends(get_db)):
    """
    Obtiene un propietario específico por ID
    BD: id_propietario, nombre, curp, rfc, telefono, email, estatus (ENUM: ACTIVO/FINADO), fecha_registro, fecha_actualizacion
    """
    sql = text("""
        SELECT
            id_propietario,
            nombre,
            curp,
            rfc,
            telefono,
            email,
            estatus,
            fecha_registro
        FROM propietarios
        WHERE id_propietario = :id_propietario
    """)

    row = db.execute(sql, {"id_propietario": id_propietario}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Propietario no encontrado")

    propietario_data = {
        "id_propietario": row["id_propietario"],
        "nombre": row["nombre"],
        "apellido_paterno": "",  # No existe en BD
        "apellido_materno": "",  # No existe en BD
        "nombre_completo": row["nombre"],
        "curp": row["curp"],
        "rfc": row["rfc"],
        "telefono": row["telefono"],
        "email": row["email"],
        "correo": row["email"],  # Alias
        "estatus": row["estatus"],
        "activo": row["estatus"] == "ACTIVO",
        "fecha_registro": row["fecha_registro"]
    }

    return propietario_data


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Crear nuevo propietario
# ==================== EMPIEZAN CAMBIOS ====================

@router.post("")
def crear_propietario(payload: PropietarioCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo propietario en el sistema
    BD: id_propietario, nombre, curp, rfc, telefono, email, estatus (ENUM: ACTIVO/FINADO), fecha_registro, fecha_actualizacion
    """
    try:
        # Validar que el CURP no exista (si se proporciona)
        if payload.curp:
            check_sql = text("""
                SELECT id_propietario FROM propietarios
                WHERE curp = :curp
            """)
            existe = db.execute(check_sql, {"curp": payload.curp.upper()}).first()

            if existe:
                raise HTTPException(
                    status_code=400,
                    detail="Ya existe un propietario con ese CURP"
                )

        # Construir nombre completo si vienen apellidos del frontend
        nombre_completo = payload.nombre
        if payload.apellido_paterno:
            nombre_completo = f"{payload.nombre} {payload.apellido_paterno}"
            if payload.apellido_materno:
                nombre_completo = f"{nombre_completo} {payload.apellido_materno}"

        # Determinar email (puede venir como email o correo del frontend)
        email_value = payload.email or (str(payload.correo) if payload.correo else None)

        # Determinar estatus
        estatus_value = payload.estatus
        if payload.activo is not None:
            estatus_value = "ACTIVO" if payload.activo else "FINADO"

        # Insertar propietario con campos reales de BD
        insert_sql = text("""
            INSERT INTO propietarios (
                nombre,
                curp,
                rfc,
                telefono,
                email,
                estatus,
                fecha_registro
            ) VALUES (
                :nombre,
                :curp,
                :rfc,
                :telefono,
                :email,
                :estatus,
                NOW()
            )
        """)

        db.execute(insert_sql, {
            "nombre": nombre_completo,
            "curp": payload.curp.upper() if payload.curp else None,
            "rfc": payload.rfc.upper() if payload.rfc else None,
            "telefono": payload.telefono,
            "email": email_value,
            "estatus": estatus_value.upper()
        })

        # Obtener ID del propietario creado
        new_id = db.execute(text("SELECT LAST_INSERT_ID() AS id")).mappings().first()["id"]

        db.commit()

        return {
            "success": True,
            "message": "Propietario creado exitosamente",
            "id_propietario": int(new_id)
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear propietario: {str(e)}")


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Actualizar propietario
# ==================== EMPIEZAN CAMBIOS ====================

@router.put("/{id_propietario}")
def actualizar_propietario(id_propietario: int, payload: PropietarioUpdate, db: Session = Depends(get_db)):
    """
    Actualiza los datos de un propietario existente
    BD: id_propietario, nombre, curp, rfc, telefono, email, estatus (ENUM: ACTIVO/FINADO), fecha_registro, fecha_actualizacion
    """
    try:
        # Verificar que el propietario existe
        check_sql = text("SELECT id_propietario FROM propietarios WHERE id_propietario = :id_propietario")
        existe = db.execute(check_sql, {"id_propietario": id_propietario}).first()

        if not existe:
            raise HTTPException(status_code=404, detail="Propietario no encontrado")

        # Construir UPDATE dinámicamente solo con campos reales de BD
        campos = []
        params = {"id_propietario": id_propietario}

        # Si vienen nombre y apellidos del frontend, combinarlos
        if payload.nombre is not None or payload.apellido_paterno is not None or payload.apellido_materno is not None:
            nombre_completo = payload.nombre or ""
            if payload.apellido_paterno:
                nombre_completo = f"{nombre_completo} {payload.apellido_paterno}".strip()
            if payload.apellido_materno:
                nombre_completo = f"{nombre_completo} {payload.apellido_materno}".strip()
            if nombre_completo:
                campos.append("nombre = :nombre")
                params["nombre"] = nombre_completo

        if payload.curp is not None:
            # Verificar que no exista otro propietario con ese CURP
            check_curp = text("""
                SELECT id_propietario FROM propietarios
                WHERE curp = :curp AND id_propietario != :id_propietario
            """)
            existe_curp = db.execute(check_curp, {
                "curp": payload.curp.upper(),
                "id_propietario": id_propietario
            }).first()

            if existe_curp:
                raise HTTPException(status_code=400, detail="Ya existe otro propietario con ese CURP")

            campos.append("curp = :curp")
            params["curp"] = payload.curp.upper()

        if payload.rfc is not None:
            campos.append("rfc = :rfc")
            params["rfc"] = payload.rfc.upper()

        if payload.telefono is not None:
            campos.append("telefono = :telefono")
            params["telefono"] = payload.telefono

        # Email puede venir como email o correo del frontend
        if payload.email is not None:
            campos.append("email = :email")
            params["email"] = payload.email
        elif payload.correo is not None:
            campos.append("email = :email")
            params["email"] = str(payload.correo)

        # Estatus puede venir como estatus o activo del frontend
        if payload.estatus is not None:
            campos.append("estatus = :estatus")
            params["estatus"] = payload.estatus.upper()
        elif payload.activo is not None:
            campos.append("estatus = :estatus")
            params["estatus"] = "ACTIVO" if payload.activo else "FINADO"

        if not campos:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        # Agregar fecha_actualizacion
        campos.append("fecha_actualizacion = NOW()")

        # Ejecutar UPDATE
        update_sql = f"""
            UPDATE propietarios
            SET {', '.join(campos)}
            WHERE id_propietario = :id_propietario
        """

        db.execute(text(update_sql), params)
        db.commit()

        return {
            "success": True,
            "message": "Propietario actualizado exitosamente"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar propietario: {str(e)}")


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Desactivar propietario (baja lógica)
# ==================== EMPIEZAN CAMBIOS ====================

@router.patch("/{id_propietario}/desactivar")
def desactivar_propietario(id_propietario: int, db: Session = Depends(get_db)):
    """
    Desactiva un propietario (cambia estatus a FINADO)
    BD usa estatus ENUM: ACTIVO/FINADO
    """
    try:
        sql = text("""
            UPDATE propietarios
            SET estatus = 'FINADO', fecha_actualizacion = NOW()
            WHERE id_propietario = :id_propietario
        """)

        result = db.execute(sql, {"id_propietario": id_propietario})
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Propietario no encontrado")

        return {
            "success": True,
            "message": "Propietario desactivado exitosamente"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al desactivar propietario: {str(e)}")


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Reactivar propietario
# ==================== EMPIEZAN CAMBIOS ====================

@router.patch("/{id_propietario}/reactivar")
def reactivar_propietario(id_propietario: int, db: Session = Depends(get_db)):
    """
    Reactiva un propietario previamente desactivado
    BD usa estatus ENUM: ACTIVO/FINADO
    """
    try:
        sql = text("""
            UPDATE propietarios
            SET estatus = 'ACTIVO', fecha_actualizacion = NOW()
            WHERE id_propietario = :id_propietario
        """)

        result = db.execute(sql, {"id_propietario": id_propietario})
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Propietario no encontrado")

        return {
            "success": True,
            "message": "Propietario reactivado exitosamente"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al reactivar propietario: {str(e)}")


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Eliminar propietario permanentemente
# ==================== EMPIEZAN CAMBIOS ====================

@router.delete("/{id_propietario}")
def eliminar_propietario(id_propietario: int, db: Session = Depends(get_db)):
    """
    Elimina permanentemente un propietario
    PRECAUCIÓN: Esta operación no se puede deshacer
    """
    try:
        sql = text("""
            DELETE FROM propietarios
            WHERE id_propietario = :id_propietario
        """)

        result = db.execute(sql, {"id_propietario": id_propietario})
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Propietario no encontrado")

        return {
            "success": True,
            "message": "Propietario eliminado permanentemente"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar propietario: {str(e)}")

# ==================== TERMINAN CAMBIOS ====================
