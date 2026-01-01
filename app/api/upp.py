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
    clave_upp: str
    nombre_predio: str
    id_propietario: int
    calle: Optional[str] = None
    municipio: str
    localidad: Optional[str] = None
    codigo_postal: Optional[str] = None
    estado: str = "Veracruz"
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    estatus: bool = True


class UppUpdate(BaseModel):
    clave_upp: Optional[str] = None
    nombre_predio: Optional[str] = None
    id_propietario: Optional[int] = None
    calle: Optional[str] = None
    municipio: Optional[str] = None
    localidad: Optional[str] = None
    codigo_postal: Optional[str] = None
    estado: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    estatus: Optional[bool] = None

# ==================== TERMINAN CAMBIOS ====================


# ==================== ENDPOINT ORIGINAL (sin cambios) ====================
@router.get("/por-clave")
def upp_por_clave(
    clave: str = Query(..., min_length=1, max_length=25),
    db: Session = Depends(get_db),
):
    c = (clave or "").strip().upper()

    sql = text("""
        SELECT
          u.id_upp,
          u.clave_upp,
          u.nombre_predio,
          u.calle,
          u.codigo_postal,
          u.estado,
          u.latitud,
          u.longitud,
          u.municipio,
          u.localidad,
          u.estatus,
          u.id_propietario,
          p.nombre AS propietario
        FROM upp u
        JOIN propietarios p ON p.id_propietario = u.id_propietario
        WHERE UPPER(u.clave_upp) = :clave
        LIMIT 1
    """)

    row = db.execute(sql, {"clave": c}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="UPP no encontrada.")

    return dict(row)


# ==================== ENDPOINT ORIGINAL (sin cambios) ====================
@router.get("")
def buscar_upp(
    search: str = Query("", max_length=120),
    limit: int = Query(15, ge=1, le=50),
    solo_activas: bool = Query(True),
    db: Session = Depends(get_db),
):
    s = (search or "").strip()
    like = f"%{s}%"

    sql = text("""
        SELECT
          u.id_upp,
          u.clave_upp,
          u.nombre_predio,
          u.municipio,
          u.localidad,
          u.estatus,
          p.nombre AS propietario
        FROM upp u
        JOIN propietarios p ON p.id_propietario = u.id_propietario
        WHERE
          (:solo_activas = 0 OR u.estatus = 1)
          AND (:s = '' OR u.clave_upp LIKE :like OR p.nombre LIKE :like OR u.nombre_predio LIKE :like)
        ORDER BY u.clave_upp ASC
        LIMIT :limit
    """)

    rows = db.execute(sql, {
        "s": s,
        "like": like,
        "limit": int(limit),
        "solo_activas": 1 if solo_activas else 0
    }).mappings().all()

    return [dict(r) for r in rows]


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Obtener UPP por ID
# ==================== EMPIEZAN CAMBIOS ====================

@router.get("/{id_upp}")
def obtener_upp(id_upp: int, db: Session = Depends(get_db)):
    """
    Obtiene una UPP específica por ID
    """
    sql = text("""
        SELECT
            u.id_upp,
            u.clave_upp,
            u.nombre_predio,
            u.calle,
            u.municipio,
            u.localidad,
            u.codigo_postal,
            u.estado,
            u.latitud,
            u.longitud,
            u.estatus,
            u.id_propietario,
            p.nombre AS propietario_nombre,
            p.apellido_paterno AS propietario_apellido_paterno,
            p.apellido_materno AS propietario_apellido_materno
        FROM upp u
        JOIN propietarios p ON p.id_propietario = u.id_propietario
        WHERE u.id_upp = :id_upp
    """)

    row = db.execute(sql, {"id_upp": id_upp}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="UPP no encontrada")

    upp = dict(row)
    upp["propietario"] = f"{upp['propietario_nombre']} {upp['propietario_apellido_paterno']} {upp.get('propietario_apellido_materno', '')}".strip()

    return upp


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Crear nueva UPP
# ==================== EMPIEZAN CAMBIOS ====================

@router.post("")
def crear_upp(payload: UppCreate, db: Session = Depends(get_db)):
    """
    Crea una nueva UPP en el sistema
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

        # Insertar UPP
        insert_sql = text("""
            INSERT INTO upp (
                clave_upp,
                nombre_predio,
                id_propietario,
                calle,
                municipio,
                localidad,
                codigo_postal,
                estado,
                latitud,
                longitud,
                estatus
            ) VALUES (
                :clave_upp,
                :nombre_predio,
                :id_propietario,
                :calle,
                :municipio,
                :localidad,
                :codigo_postal,
                :estado,
                :latitud,
                :longitud,
                :estatus
            )
        """)

        db.execute(insert_sql, {
            "clave_upp": payload.clave_upp.upper(),
            "nombre_predio": payload.nombre_predio,
            "id_propietario": payload.id_propietario,
            "calle": payload.calle,
            "municipio": payload.municipio,
            "localidad": payload.localidad,
            "codigo_postal": payload.codigo_postal,
            "estado": payload.estado,
            "latitud": payload.latitud,
            "longitud": payload.longitud,
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
    """
    try:
        # Verificar que la UPP existe
        check_sql = text("SELECT id_upp FROM upp WHERE id_upp = :id_upp")
        existe = db.execute(check_sql, {"id_upp": id_upp}).first()

        if not existe:
            raise HTTPException(status_code=404, detail="UPP no encontrada")

        # Construir UPDATE dinámicamente
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

        if payload.nombre_predio is not None:
            campos.append("nombre_predio = :nombre_predio")
            params["nombre_predio"] = payload.nombre_predio

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

        if payload.calle is not None:
            campos.append("calle = :calle")
            params["calle"] = payload.calle

        if payload.municipio is not None:
            campos.append("municipio = :municipio")
            params["municipio"] = payload.municipio

        if payload.localidad is not None:
            campos.append("localidad = :localidad")
            params["localidad"] = payload.localidad

        if payload.codigo_postal is not None:
            campos.append("codigo_postal = :codigo_postal")
            params["codigo_postal"] = payload.codigo_postal

        if payload.estado is not None:
            campos.append("estado = :estado")
            params["estado"] = payload.estado

        if payload.latitud is not None:
            campos.append("latitud = :latitud")
            params["latitud"] = payload.latitud

        if payload.longitud is not None:
            campos.append("longitud = :longitud")
            params["longitud"] = payload.longitud

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
