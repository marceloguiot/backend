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
    # Campos que existen en la BD real
    nombre: str
    curp: Optional[str] = None
    rfc: Optional[str] = None
    telefono: Optional[str] = None
    estatus: str = "ACTIVO"  # ACTIVO o FINADO

    # Campos del frontend que no existen en BD (se ignoran o mapean)
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    correo: Optional[EmailStr] = None
    calle: Optional[str] = None
    municipio: Optional[str] = None
    localidad: Optional[str] = None
    cp: Optional[str] = None
    estado: Optional[str] = None
    activo: Optional[bool] = None


class PropietarioUpdate(BaseModel):
    # Campos que existen en la BD real
    nombre: Optional[str] = None
    curp: Optional[str] = None
    rfc: Optional[str] = None
    telefono: Optional[str] = None
    estatus: Optional[str] = None

    # Campos del frontend que no existen en BD (se ignoran o mapean)
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    correo: Optional[EmailStr] = None
    calle: Optional[str] = None
    municipio: Optional[str] = None
    localidad: Optional[str] = None
    cp: Optional[str] = None
    estado: Optional[str] = None
    activo: Optional[bool] = None

# ==================== TERMINAN CAMBIOS ====================


# ==================== ENDPOINT ORIGINAL (sin cambios) ====================
@router.get("/por-curp")
def propietario_por_curp(curp: str, db: Session = Depends(get_db)):
    curp = (curp or "").strip().upper()
    if not curp:
        raise HTTPException(status_code=400, detail="CURP requerida")

    q = text("""
        SELECT
            id_propietario,
            nombre,
            curp,
            rfc,
            telefono,
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
        "correo": "",  # No existe en BD real
        "calle": "",  # No existe en BD real
        "municipio": "",  # No existe en BD real
        "localidad": "",  # No existe en BD real
        "cp": "",  # No existe en BD real
        "estado": "",  # No existe en BD real
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
    Usa la estructura real de la BD: nombre, curp, rfc, telefono, estatus
    """
    sql = """
        SELECT DISTINCT
            p.id_propietario,
            p.nombre,
            p.curp,
            p.rfc,
            p.telefono,
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
            "correo": "",  # No existe en BD real
            "calle": "",  # No existe en BD real
            "municipio": "",  # No existe en BD real
            "localidad": "",  # No existe en BD real
            "cp": "",  # No existe en BD real
            "estado": "",  # No existe en BD real
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
    """
    sql = text("""
        SELECT
            id_propietario,
            nombre,
            apellido_paterno,
            apellido_materno,
            curp,
            telefono,
            correo,
            calle,
            municipio,
            localidad,
            cp,
            estado,
            activo
        FROM propietarios
        WHERE id_propietario = :id_propietario
    """)

    row = db.execute(sql, {"id_propietario": id_propietario}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Propietario no encontrado")

    propietario = dict(row)
    propietario["nombre_completo"] = f"{propietario['nombre']} {propietario['apellido_paterno']} {propietario.get('apellido_materno', '')}".strip()

    return propietario


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Crear nuevo propietario
# ==================== EMPIEZAN CAMBIOS ====================

@router.post("")
def crear_propietario(payload: PropietarioCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo propietario en el sistema
    """
    try:
        # Validar que el CURP no exista
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

        # Insertar propietario
        insert_sql = text("""
            INSERT INTO propietarios (
                nombre,
                apellido_paterno,
                apellido_materno,
                curp,
                telefono,
                correo,
                calle,
                municipio,
                localidad,
                cp,
                estado,
                activo
            ) VALUES (
                :nombre,
                :apellido_paterno,
                :apellido_materno,
                :curp,
                :telefono,
                :correo,
                :calle,
                :municipio,
                :localidad,
                :cp,
                :estado,
                :activo
            )
        """)

        db.execute(insert_sql, {
            "nombre": payload.nombre,
            "apellido_paterno": payload.apellido_paterno,
            "apellido_materno": payload.apellido_materno,
            "curp": payload.curp.upper(),
            "telefono": payload.telefono,
            "correo": payload.correo,
            "calle": payload.calle,
            "municipio": payload.municipio,
            "localidad": payload.localidad,
            "cp": payload.cp,
            "estado": payload.estado,
            "activo": 1 if payload.activo else 0
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
    """
    try:
        # Verificar que el propietario existe
        check_sql = text("SELECT id_propietario FROM propietarios WHERE id_propietario = :id_propietario")
        existe = db.execute(check_sql, {"id_propietario": id_propietario}).first()

        if not existe:
            raise HTTPException(status_code=404, detail="Propietario no encontrado")

        # Construir UPDATE dinámicamente
        campos = []
        params = {"id_propietario": id_propietario}

        if payload.nombre is not None:
            campos.append("nombre = :nombre")
            params["nombre"] = payload.nombre

        if payload.apellido_paterno is not None:
            campos.append("apellido_paterno = :apellido_paterno")
            params["apellido_paterno"] = payload.apellido_paterno

        if payload.apellido_materno is not None:
            campos.append("apellido_materno = :apellido_materno")
            params["apellido_materno"] = payload.apellido_materno

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

        if payload.telefono is not None:
            campos.append("telefono = :telefono")
            params["telefono"] = payload.telefono

        if payload.correo is not None:
            campos.append("correo = :correo")
            params["correo"] = payload.correo

        if payload.calle is not None:
            campos.append("calle = :calle")
            params["calle"] = payload.calle

        if payload.municipio is not None:
            campos.append("municipio = :municipio")
            params["municipio"] = payload.municipio

        if payload.localidad is not None:
            campos.append("localidad = :localidad")
            params["localidad"] = payload.localidad

        if payload.cp is not None:
            campos.append("cp = :cp")
            params["cp"] = payload.cp

        if payload.estado is not None:
            campos.append("estado = :estado")
            params["estado"] = payload.estado

        if payload.activo is not None:
            campos.append("activo = :activo")
            params["activo"] = 1 if payload.activo else 0

        if not campos:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

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
    Desactiva un propietario (baja lógica)
    """
    try:
        sql = text("""
            UPDATE propietarios
            SET activo = 0
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
    """
    try:
        sql = text("""
            UPDATE propietarios
            SET activo = 1
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
