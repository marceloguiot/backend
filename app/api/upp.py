# backend/app/api/upp.py
# ==================== EMPIEZAN CAMBIOS ====================
# Se agregaron imports para modelos Pydantic y Optional
# ==================== EMPIEZAN CAMBIOS ====================
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.database import get_db

router = APIRouter(prefix="/api/upp", tags=["upp"])


# ==================== EMPIEZAN CAMBIOS ====================
# Modelos Pydantic para UPP
# ==================== EMPIEZAN CAMBIOS ====================

class UppCreate(BaseModel):
    # BD: id_upp, clave_upp, id_propietario, id_municipio, localidad, direccion, telefono_contacto, estatus, fecha_registro
    clave_upp: str
    id_propietario: int
    id_municipio: Optional[int] = None
    localidad: Optional[str] = None
    direccion: Optional[str] = None
    telefono_contacto: Optional[str] = None
    estatus: bool = True

    # Campos del frontend que se mapean
    municipio: Optional[str] = None  # Se puede usar para buscar id_municipio


class UppUpdate(BaseModel):
    # BD: id_upp, clave_upp, id_propietario, id_municipio, localidad, direccion, telefono_contacto, estatus, fecha_registro
    clave_upp: Optional[str] = None
    id_propietario: Optional[int] = None
    id_municipio: Optional[int] = None
    localidad: Optional[str] = None
    direccion: Optional[str] = None
    telefono_contacto: Optional[str] = None
    estatus: Optional[bool] = None

    # Campos del frontend que se mapean
    municipio: Optional[str] = None  # Se puede usar para buscar id_municipio

# ==================== TERMINAN CAMBIOS ====================


# ==================== ENDPOINT ORIGINAL (sin cambios) ====================
@router.get("/por-clave")
def upp_por_clave(
    clave: str = Query(..., min_length=1, max_length=25),
    db: Session = Depends(get_db),
):
    """
    BD: id_upp, clave_upp, id_propietario, id_municipio, localidad, direccion, telefono_contacto, estatus, fecha_registro
    """
    c = (clave or "").strip().upper()

    sql = text("""
        SELECT
          u.id_upp,
          u.clave_upp,
          u.id_propietario,
          u.id_municipio,
          u.localidad,
          u.direccion,
          u.telefono_contacto,
          u.estatus,
          u.fecha_registro,
          p.nombre AS propietario,
          m.nombre AS municipio_nombre,
          e.nombre AS estado_nombre
        FROM upp u
        INNER JOIN propietarios p ON p.id_propietario = u.id_propietario
        LEFT JOIN cat_municipio m ON m.id_municipio = u.id_municipio
        LEFT JOIN cat_estado e ON e.id_estado = m.id_estado
        WHERE UPPER(u.clave_upp) = :clave
        LIMIT 1
    """)

    row = db.execute(sql, {"clave": c}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="UPP no encontrada.")

    # Mapear campos reales de BD a campos esperados por frontend
    upp_data = {
        "id_upp": row["id_upp"],
        "clave_upp": row["clave_upp"],
        "id_propietario": row["id_propietario"],
        "propietario": row["propietario"],
        "id_municipio": row["id_municipio"],
        "municipio": row["municipio_nombre"],  # Nombre del municipio para frontend
        "localidad": row["localidad"],
        "direccion": row["direccion"],
        "nombre_predio": row["direccion"] or row["clave_upp"],  # Alias para frontend
        "telefono_contacto": row["telefono_contacto"],
        "estatus": bool(row["estatus"]),
        "fecha_registro": row["fecha_registro"],
        "estado": row["estado_nombre"]  # Nombre del estado para frontend
    }

    return upp_data


@router.get("")
def buscar_upp(
    search: str = Query("", max_length=120),
    limit: int = Query(15, ge=1, le=50),
    solo_activas: bool = Query(True),
    db: Session = Depends(get_db),
):
    """
    BD: id_upp, clave_upp, id_propietario, id_municipio, localidad, direccion, telefono_contacto, estatus, fecha_registro
    """
    s = (search or "").strip()
    like = f"%{s}%"

    sql = text("""
        SELECT
          u.id_upp,
          u.clave_upp,
          u.id_propietario,
          u.id_municipio,
          u.localidad,
          u.direccion,
          u.telefono_contacto,
          u.estatus,
          u.fecha_registro,
          p.nombre AS propietario,
          m.nombre AS municipio_nombre,
          e.nombre AS estado_nombre
        FROM upp u
        INNER JOIN propietarios p ON p.id_propietario = u.id_propietario
        LEFT JOIN cat_municipio m ON m.id_municipio = u.id_municipio
        LEFT JOIN cat_estado e ON e.id_estado = m.id_estado
        WHERE
          (:solo_activas = 0 OR u.estatus = 1)
          AND (:s = '' OR u.clave_upp LIKE :like OR p.nombre LIKE :like)
        ORDER BY u.clave_upp ASC
        LIMIT :limit
    """)

    rows = db.execute(sql, {
        "s": s,
        "like": like,
        "limit": int(limit),
        "solo_activas": 1 if solo_activas else 0
    }).mappings().all()

    # Mapear campos reales de BD a campos esperados por frontend
    upps = []
    for row in rows:
        upp_data = {
            "id_upp": row["id_upp"],
            "clave_upp": row["clave_upp"],
            "id_propietario": row["id_propietario"],
            "propietario": row["propietario"],
            "id_municipio": row["id_municipio"],
            "municipio": row["municipio_nombre"],
            "localidad": row["localidad"],
            "direccion": row["direccion"],
            "nombre_predio": row["direccion"] or row["clave_upp"],  # Alias para frontend
            "telefono_contacto": row["telefono_contacto"],
            "estatus": bool(row["estatus"]),
            "fecha_registro": row["fecha_registro"],
            "estado": row["estado_nombre"]
        }
        upps.append(upp_data)

    return upps


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Obtener UPP por ID
# ==================== EMPIEZAN CAMBIOS ====================

@router.get("/{id_upp}")
def obtener_upp(id_upp: int, db: Session = Depends(get_db)):
    """
    Obtiene una UPP específica por ID
    BD: id_upp, clave_upp, id_propietario, id_municipio, localidad, direccion, telefono_contacto, estatus, fecha_registro
    """
    sql = text("""
        SELECT
            u.id_upp,
            u.clave_upp,
            u.id_propietario,
            u.id_municipio,
            u.localidad,
            u.direccion,
            u.telefono_contacto,
            u.estatus,
            u.fecha_registro,
            p.nombre AS propietario,
            m.nombre AS municipio_nombre,
            e.nombre AS estado_nombre
        FROM upp u
        INNER JOIN propietarios p ON p.id_propietario = u.id_propietario
        LEFT JOIN cat_municipio m ON m.id_municipio = u.id_municipio
        LEFT JOIN cat_estado e ON e.id_estado = m.id_estado
        WHERE u.id_upp = :id_upp
    """)

    row = db.execute(sql, {"id_upp": id_upp}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="UPP no encontrada")

    upp_data = {
        "id_upp": row["id_upp"],
        "clave_upp": row["clave_upp"],
        "id_propietario": row["id_propietario"],
        "propietario": row["propietario"],
        "id_municipio": row["id_municipio"],
        "municipio": row["municipio_nombre"],
        "localidad": row["localidad"],
        "direccion": row["direccion"],
        "nombre_predio": row["direccion"] or row["clave_upp"],  # Alias para frontend
        "telefono_contacto": row["telefono_contacto"],
        "estatus": bool(row["estatus"]),
        "fecha_registro": row["fecha_registro"],
        "estado": row["estado_nombre"]
    }

    return upp_data


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Crear nueva UPP
# ==================== EMPIEZAN CAMBIOS ====================

@router.post("")
def crear_upp(payload: UppCreate, db: Session = Depends(get_db)):
    """
    Crea una nueva UPP en el sistema
    BD: id_upp, clave_upp, id_propietario, id_municipio, localidad, direccion, telefono_contacto, estatus, fecha_registro
    """
    try:
        # Validar que la clave UPP no exista
        check_sql = text("""
            SELECT id_upp FROM upp
            WHERE clave_upp = :clave_upp
        """)
        existe = db.execute(check_sql, {"clave_upp": payload.clave_upp.upper()}).first()

        if existe:
            raise HTTPException(
                status_code=400,
                detail="Ya existe una UPP con esa clave"
            )

        # Validar que el propietario existe
        check_propietario = text("""
            SELECT id_propietario FROM propietarios
            WHERE id_propietario = :id_propietario
        """)
        propietario = db.execute(check_propietario, {"id_propietario": payload.id_propietario}).first()

        if not propietario:
            raise HTTPException(
                status_code=404,
                detail="El propietario especificado no existe"
            )

        # Determinar id_municipio (puede venir directo o buscarse por nombre)
        id_municipio = payload.id_municipio
        if not id_municipio and payload.municipio:
            # Buscar municipio por nombre
            muni_sql = text("SELECT id_municipio FROM cat_municipio WHERE nombre LIKE :nombre LIMIT 1")
            muni_row = db.execute(muni_sql, {"nombre": f"%{payload.municipio}%"}).first()
            if muni_row:
                id_municipio = muni_row[0]

        # Insertar UPP con campos reales de BD
        insert_sql = text("""
            INSERT INTO upp (
                clave_upp,
                id_propietario,
                id_municipio,
                localidad,
                direccion,
                telefono_contacto,
                estatus,
                fecha_registro
            ) VALUES (
                :clave_upp,
                :id_propietario,
                :id_municipio,
                :localidad,
                :direccion,
                :telefono_contacto,
                :estatus,
                NOW()
            )
        """)

        db.execute(insert_sql, {
            "clave_upp": payload.clave_upp.upper(),
            "id_propietario": payload.id_propietario,
            "id_municipio": id_municipio,
            "localidad": payload.localidad,
            "direccion": payload.direccion,
            "telefono_contacto": payload.telefono_contacto,
            "estatus": 1 if payload.estatus else 0
        })

        # Obtener ID de la UPP creada
        new_id = db.execute(text("SELECT LAST_INSERT_ID() AS id")).mappings().first()["id"]

        db.commit()

        return {
            "success": True,
            "message": "UPP creada exitosamente",
            "id_upp": int(new_id)
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear UPP: {str(e)}")


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Actualizar UPP
# ==================== EMPIEZAN CAMBIOS ====================

@router.put("/{id_upp}")
def actualizar_upp(id_upp: int, payload: UppUpdate, db: Session = Depends(get_db)):
    """
    Actualiza los datos de una UPP existente
    BD: id_upp, clave_upp, id_propietario, id_municipio, localidad, direccion, telefono_contacto, estatus, fecha_registro
    """
    try:
        # Verificar que la UPP existe
        check_sql = text("SELECT id_upp FROM upp WHERE id_upp = :id_upp")
        existe = db.execute(check_sql, {"id_upp": id_upp}).first()

        if not existe:
            raise HTTPException(status_code=404, detail="UPP no encontrada")

        # Construir UPDATE dinámicamente solo con campos reales de BD
        campos = []
        params = {"id_upp": id_upp}

        if payload.clave_upp is not None:
            # Verificar que no exista otra UPP con esa clave
            check_clave = text("""
                SELECT id_upp FROM upp
                WHERE clave_upp = :clave_upp AND id_upp != :id_upp
            """)
            existe_clave = db.execute(check_clave, {
                "clave_upp": payload.clave_upp.upper(),
                "id_upp": id_upp
            }).first()

            if existe_clave:
                raise HTTPException(status_code=400, detail="Ya existe otra UPP con esa clave")

            campos.append("clave_upp = :clave_upp")
            params["clave_upp"] = payload.clave_upp.upper()

        if payload.id_propietario is not None:
            # Verificar que el propietario existe
            check_propietario = text("""
                SELECT id_propietario FROM propietarios
                WHERE id_propietario = :id_propietario
            """)
            propietario = db.execute(check_propietario, {"id_propietario": payload.id_propietario}).first()

            if not propietario:
                raise HTTPException(status_code=404, detail="El propietario especificado no existe")

            campos.append("id_propietario = :id_propietario")
            params["id_propietario"] = payload.id_propietario

        # Determinar id_municipio (puede venir directo o buscarse por nombre)
        if payload.id_municipio is not None:
            campos.append("id_municipio = :id_municipio")
            params["id_municipio"] = payload.id_municipio
        elif payload.municipio is not None:
            # Buscar municipio por nombre
            muni_sql = text("SELECT id_municipio FROM cat_municipio WHERE nombre LIKE :nombre LIMIT 1")
            muni_row = db.execute(muni_sql, {"nombre": f"%{payload.municipio}%"}).first()
            if muni_row:
                campos.append("id_municipio = :id_municipio")
                params["id_municipio"] = muni_row[0]

        if payload.localidad is not None:
            campos.append("localidad = :localidad")
            params["localidad"] = payload.localidad

        if payload.direccion is not None:
            campos.append("direccion = :direccion")
            params["direccion"] = payload.direccion

        if payload.telefono_contacto is not None:
            campos.append("telefono_contacto = :telefono_contacto")
            params["telefono_contacto"] = payload.telefono_contacto

        if payload.estatus is not None:
            campos.append("estatus = :estatus")
            params["estatus"] = 1 if payload.estatus else 0

        if not campos:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        # Ejecutar UPDATE
        update_sql = f"""
            UPDATE upp
            SET {', '.join(campos)}
            WHERE id_upp = :id_upp
        """

        db.execute(text(update_sql), params)
        db.commit()

        return {
            "success": True,
            "message": "UPP actualizada exitosamente"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar UPP: {str(e)}")


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Dar de baja UPP (baja lógica)
# ==================== EMPIEZAN CAMBIOS ====================

@router.patch("/{id_upp}/dar-baja")
def dar_baja_upp(id_upp: int, db: Session = Depends(get_db)):
    """
    Da de baja una UPP (baja lógica)
    """
    try:
        sql = text("""
            UPDATE upp
            SET estatus = 0
            WHERE id_upp = :id_upp
        """)

        result = db.execute(sql, {"id_upp": id_upp})
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="UPP no encontrada")

        return {
            "success": True,
            "message": "UPP dada de baja exitosamente"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al dar de baja UPP: {str(e)}")


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Reactivar UPP
# ==================== EMPIEZAN CAMBIOS ====================

@router.patch("/{id_upp}/reactivar")
def reactivar_upp(id_upp: int, db: Session = Depends(get_db)):
    """
    Reactiva una UPP previamente dada de baja
    """
    try:
        sql = text("""
            UPDATE upp
            SET estatus = 1
            WHERE id_upp = :id_upp
        """)

        result = db.execute(sql, {"id_upp": id_upp})
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="UPP no encontrada")

        return {
            "success": True,
            "message": "UPP reactivada exitosamente"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al reactivar UPP: {str(e)}")


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Eliminar UPP permanentemente
# ==================== EMPIEZAN CAMBIOS ====================

@router.delete("/{id_upp}")
def eliminar_upp(id_upp: int, db: Session = Depends(get_db)):
    """
    Elimina permanentemente una UPP
    PRECAUCIÓN: Esta operación no se puede deshacer
    """
    try:
        sql = text("""
            DELETE FROM upp
            WHERE id_upp = :id_upp
        """)

        result = db.execute(sql, {"id_upp": id_upp})
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="UPP no encontrada")

        return {
            "success": True,
            "message": "UPP eliminada permanentemente"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar UPP: {str(e)}")

# ==================== TERMINAN CAMBIOS ====================
