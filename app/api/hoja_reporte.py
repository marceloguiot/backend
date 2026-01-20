# ==================== ARCHIVO NUEVO ====================
# Endpoint para hojas de reporte
# ==================== ARCHIVO NUEVO ====================

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import date

from app.db.database import get_db

router = APIRouter(prefix="/api/hoja-reporte", tags=["hoja-reporte"])


# ==================== Modelos Pydantic ====================

class HojaReporteCreate(BaseModel):
    # Campos basados en estructura típica de hoja de reporte
    folio: Optional[str] = None
    id_caso: Optional[int] = None
    id_usuario_mvz: Optional[int] = None
    fecha_reporte: date
    observaciones: Optional[str] = None


class HojaReporteUpdate(BaseModel):
    folio: Optional[str] = None
    id_caso: Optional[int] = None
    id_usuario_mvz: Optional[int] = None
    fecha_reporte: Optional[date] = None
    observaciones: Optional[str] = None


# ==================== Endpoints ====================

@router.get("")
def consultar_hojas_reporte(
    folio: Optional[str] = None,
    id_caso: Optional[int] = None,
    numero_caso: Optional[str] = None,
    mvz: Optional[str] = None,
    upp: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    fecha: Optional[date] = None,  # Alias para fecha exacta
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Consulta hojas de reporte con filtros opcionales
    """
    # Query completo con todas las relaciones necesarias
    sql = """
        SELECT
            hr.id_hoja_reporte,
            hr.folio,
            hr.id_caso,
            hr.id_usuario_mvz,
            hr.fecha_reporte,
            hr.observaciones,
            hr.created_at,
            c.numero_caso,
            u_mvz.nombre AS mvz_nombre,
            u_mvz.usuario AS mvz_usuario,
            upp.clave_upp,
            upp.id_upp,
            p.nombre AS propietario
        FROM hoja_reporte hr
        LEFT JOIN casos c ON c.id_caso = hr.id_caso
        LEFT JOIN usuarios u_mvz ON u_mvz.id_usuario = hr.id_usuario_mvz
        LEFT JOIN upp ON upp.id_upp = c.id_upp
        LEFT JOIN propietarios p ON p.id_propietario = upp.id_propietario
        WHERE 1=1
    """
    params = {"limit": int(limit)}

    if folio:
        sql += " AND hr.folio LIKE :folio"
        params["folio"] = f"%{folio.strip()}%"

    if id_caso:
        sql += " AND hr.id_caso = :id_caso"
        params["id_caso"] = id_caso

    if numero_caso:
        sql += " AND c.numero_caso LIKE :numero_caso"
        params["numero_caso"] = f"%{numero_caso.strip()}%"

    if mvz:
        sql += " AND (u_mvz.nombre LIKE :mvz OR u_mvz.usuario LIKE :mvz)"
        params["mvz"] = f"%{mvz.strip()}%"

    if upp:
        sql += " AND upp.clave_upp LIKE :upp"
        params["upp"] = f"%{upp.strip()}%"

    if fecha:
        sql += " AND hr.fecha_reporte = :fecha"
        params["fecha"] = fecha

    if fecha_desde:
        sql += " AND hr.fecha_reporte >= :fecha_desde"
        params["fecha_desde"] = fecha_desde

    if fecha_hasta:
        sql += " AND hr.fecha_reporte <= :fecha_hasta"
        params["fecha_hasta"] = fecha_hasta

    sql += " ORDER BY hr.id_hoja_reporte DESC LIMIT :limit"

    rows = db.execute(text(sql), params).mappings().all()

    # Mapear a formato esperado por frontend
    hojas = []
    for row in rows:
        hoja_data = {
            "id": row["id_hoja_reporte"],
            "id_hoja_reporte": row["id_hoja_reporte"],
            "folio": row["folio"],
            "id_caso": row["id_caso"],
            "numero_caso": row["numero_caso"],
            "id_usuario_mvz": row["id_usuario_mvz"],
            "mvz": row["mvz_nombre"] or row["mvz_usuario"] or "",  # Nombre para frontend
            "mvz_nombre": row["mvz_nombre"],
            "mvz_usuario": row["mvz_usuario"],
            "fecha": str(row["fecha_reporte"]) if row["fecha_reporte"] else "",  # Alias para frontend
            "fecha_reporte": row["fecha_reporte"],
            "upp": row["clave_upp"] or "",  # Nombre para frontend
            "clave_upp": row["clave_upp"],
            "id_upp": row["id_upp"],
            "propietario": row["propietario"],
            "obs": row["observaciones"] or "",  # Alias para frontend
            "observaciones": row["observaciones"],
            "created_at": row["created_at"]
        }
        hojas.append(hoja_data)

    return hojas


@router.get("/{id_hoja_reporte}")
def obtener_hoja_reporte(id_hoja_reporte: int, db: Session = Depends(get_db)):
    """
    Obtiene una hoja de reporte específica por ID
    """
    sql = text("""
        SELECT
            hr.id_hoja_reporte,
            hr.folio,
            hr.id_caso,
            hr.id_usuario_mvz,
            hr.fecha_reporte,
            hr.observaciones,
            hr.created_at,
            c.numero_caso,
            u_mvz.nombre AS mvz_nombre,
            u_mvz.usuario AS mvz_usuario,
            upp.clave_upp,
            upp.id_upp,
            p.nombre AS propietario
        FROM hoja_reporte hr
        LEFT JOIN casos c ON c.id_caso = hr.id_caso
        LEFT JOIN usuarios u_mvz ON u_mvz.id_usuario = hr.id_usuario_mvz
        LEFT JOIN upp ON upp.id_upp = c.id_upp
        LEFT JOIN propietarios p ON p.id_propietario = upp.id_propietario
        WHERE hr.id_hoja_reporte = :id_hoja_reporte
    """)

    row = db.execute(sql, {"id_hoja_reporte": id_hoja_reporte}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Hoja de reporte no encontrada")

    hoja_data = {
        "id": row["id_hoja_reporte"],
        "id_hoja_reporte": row["id_hoja_reporte"],
        "folio": row["folio"],
        "id_caso": row["id_caso"],
        "numero_caso": row["numero_caso"],
        "id_usuario_mvz": row["id_usuario_mvz"],
        "mvz": row["mvz_nombre"] or row["mvz_usuario"] or "",
        "mvz_nombre": row["mvz_nombre"],
        "mvz_usuario": row["mvz_usuario"],
        "fecha": str(row["fecha_reporte"]) if row["fecha_reporte"] else "",
        "fecha_reporte": row["fecha_reporte"],
        "upp": row["clave_upp"] or "",
        "clave_upp": row["clave_upp"],
        "id_upp": row["id_upp"],
        "propietario": row["propietario"],
        "obs": row["observaciones"] or "",
        "observaciones": row["observaciones"],
        "created_at": row["created_at"]
    }

    return hoja_data


@router.post("")
def crear_hoja_reporte(payload: HojaReporteCreate, db: Session = Depends(get_db)):
    """
    Crea una nueva hoja de reporte
    """
    try:
        insert_sql = text("""
            INSERT INTO hoja_reporte (
                folio,
                id_caso,
                id_usuario_mvz,
                fecha_reporte,
                observaciones,
                created_at
            ) VALUES (
                :folio,
                :id_caso,
                :id_usuario_mvz,
                :fecha_reporte,
                :observaciones,
                NOW()
            )
        """)

        db.execute(insert_sql, {
            "folio": payload.folio,
            "id_caso": payload.id_caso,
            "id_usuario_mvz": payload.id_usuario_mvz,
            "fecha_reporte": payload.fecha_reporte,
            "observaciones": payload.observaciones
        })

        new_id = db.execute(text("SELECT LAST_INSERT_ID() AS id")).mappings().first()["id"]
        db.commit()

        return {
            "success": True,
            "message": "Hoja de reporte creada exitosamente",
            "id_hoja_reporte": int(new_id)
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear hoja de reporte: {str(e)}")


@router.put("/{id_hoja_reporte}")
def actualizar_hoja_reporte(id_hoja_reporte: int, payload: HojaReporteUpdate, db: Session = Depends(get_db)):
    """
    Actualiza una hoja de reporte existente
    """
    try:
        check_sql = text("SELECT id_hoja_reporte FROM hoja_reporte WHERE id_hoja_reporte = :id_hoja_reporte")
        existe = db.execute(check_sql, {"id_hoja_reporte": id_hoja_reporte}).first()

        if not existe:
            raise HTTPException(status_code=404, detail="Hoja de reporte no encontrada")

        campos = []
        params = {"id_hoja_reporte": id_hoja_reporte}

        if payload.folio is not None:
            campos.append("folio = :folio")
            params["folio"] = payload.folio

        if payload.id_caso is not None:
            campos.append("id_caso = :id_caso")
            params["id_caso"] = payload.id_caso

        if payload.id_usuario_mvz is not None:
            campos.append("id_usuario_mvz = :id_usuario_mvz")
            params["id_usuario_mvz"] = payload.id_usuario_mvz

        if payload.fecha_reporte is not None:
            campos.append("fecha_reporte = :fecha_reporte")
            params["fecha_reporte"] = payload.fecha_reporte

        if payload.observaciones is not None:
            campos.append("observaciones = :observaciones")
            params["observaciones"] = payload.observaciones

        if not campos:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        update_sql = f"""
            UPDATE hoja_reporte
            SET {', '.join(campos)}
            WHERE id_hoja_reporte = :id_hoja_reporte
        """

        db.execute(text(update_sql), params)
        db.commit()

        return {
            "success": True,
            "message": "Hoja de reporte actualizada exitosamente"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar hoja de reporte: {str(e)}")


@router.delete("/{id_hoja_reporte}")
def eliminar_hoja_reporte(id_hoja_reporte: int, db: Session = Depends(get_db)):
    """
    Elimina una hoja de reporte
    """
    try:
        sql = text("""
            DELETE FROM hoja_reporte
            WHERE id_hoja_reporte = :id_hoja_reporte
        """)

        result = db.execute(sql, {"id_hoja_reporte": id_hoja_reporte})
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Hoja de reporte no encontrada")

        return {
            "success": True,
            "message": "Hoja de reporte eliminada exitosamente"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar hoja de reporte: {str(e)}")
