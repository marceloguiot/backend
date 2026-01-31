# ==================== ARCHIVO CORREGIDO ====================
# Endpoint para hojas de reporte
# BD: id_reporte, folio, periodo_inicio, periodo_fin, contenido, archivo, fecha, id_usuario
# ==================== ARCHIVO CORREGIDO ====================

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
import json

from app.db.database import get_db

router = APIRouter(prefix="/api/hoja-reporte", tags=["hoja-reporte"])


# ==================== Modelos Pydantic ====================

class HojaReporteCreate(BaseModel):
    # BD: id_reporte, folio, periodo_inicio, periodo_fin, contenido, archivo, fecha, id_usuario
    folio: Optional[str] = None
    periodo_inicio: Optional[date] = None
    periodo_fin: Optional[date] = None
    contenido: Optional[dict] = None  # JSON
    archivo: Optional[str] = None
    id_usuario: int


class HojaReporteUpdate(BaseModel):
    folio: Optional[str] = None
    periodo_inicio: Optional[date] = None
    periodo_fin: Optional[date] = None
    contenido: Optional[dict] = None
    archivo: Optional[str] = None


# ==================== Endpoints ====================

@router.get("")
def consultar_hojas_reporte(
    folio: Optional[str] = None,
    periodo_inicio: Optional[date] = None,
    periodo_fin: Optional[date] = None,
    id_usuario: Optional[int] = None,
    mvz: Optional[str] = None,  # Filtro por nombre de usuario (para compatibilidad con frontend)
    fecha: Optional[date] = None,  # Filtro por fecha exacta (para compatibilidad con frontend)
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Consulta hojas de reporte con filtros opcionales
    BD: id_reporte, folio, periodo_inicio, periodo_fin, contenido, archivo, fecha, id_usuario
    """
    sql = """
        SELECT
            hr.id_reporte,
            hr.folio,
            hr.periodo_inicio,
            hr.periodo_fin,
            hr.contenido,
            hr.archivo,
            hr.fecha,
            hr.id_usuario,
            u.nombre AS usuario_nombre,
            u.usuario AS usuario_login
        FROM hoja_reporte hr
        LEFT JOIN usuarios u ON u.id_usuario = hr.id_usuario
        WHERE 1=1
    """
    params = {"limit": int(limit)}

    if folio:
        sql += " AND hr.folio LIKE :folio"
        params["folio"] = f"%{folio.strip()}%"

    if periodo_inicio:
        sql += " AND hr.periodo_inicio >= :periodo_inicio"
        params["periodo_inicio"] = periodo_inicio

    if periodo_fin:
        sql += " AND hr.periodo_fin <= :periodo_fin"
        params["periodo_fin"] = periodo_fin

    if id_usuario:
        sql += " AND hr.id_usuario = :id_usuario"
        params["id_usuario"] = id_usuario

    if mvz:
        sql += " AND u.nombre LIKE :mvz"
        params["mvz"] = f"%{mvz.strip()}%"

    if fecha:
        sql += " AND DATE(hr.fecha) = :fecha"
        params["fecha"] = fecha

    if fecha_desde:
        sql += " AND hr.fecha >= :fecha_desde"
        params["fecha_desde"] = fecha_desde

    if fecha_hasta:
        sql += " AND hr.fecha <= :fecha_hasta"
        params["fecha_hasta"] = fecha_hasta

    sql += " ORDER BY hr.id_reporte DESC LIMIT :limit"

    rows = db.execute(text(sql), params).mappings().all()

    # Mapear a formato esperado por frontend
    hojas = []
    for row in rows:
        # Parsear contenido JSON si existe
        contenido = row["contenido"]
        if contenido and isinstance(contenido, str):
            try:
                contenido = json.loads(contenido)
            except:
                contenido = {}

        hoja_data = {
            "id": row["id_reporte"],
            "id_reporte": row["id_reporte"],
            "id_hoja_reporte": row["id_reporte"],  # Alias para compatibilidad
            "folio": row["folio"],
            "periodo_inicio": row["periodo_inicio"],
            "periodo_fin": row["periodo_fin"],
            "contenido": contenido,
            "archivo": row["archivo"],
            "fecha": row["fecha"],
            "id_usuario": row["id_usuario"],
            "usuario_nombre": row["usuario_nombre"],
            "usuario": row["usuario_login"],
            # Campos para compatibilidad con frontend anterior
            "mvz": row["usuario_nombre"] or "",
            "upp": "",  # No existe en esta tabla
            "obs": ""  # No existe en esta tabla
        }
        hojas.append(hoja_data)

    return hojas


@router.get("/{id_reporte}")
def obtener_hoja_reporte(id_reporte: int, db: Session = Depends(get_db)):
    """
    Obtiene una hoja de reporte específica por ID
    BD: id_reporte, folio, periodo_inicio, periodo_fin, contenido, archivo, fecha, id_usuario
    """
    sql = text("""
        SELECT
            hr.id_reporte,
            hr.folio,
            hr.periodo_inicio,
            hr.periodo_fin,
            hr.contenido,
            hr.archivo,
            hr.fecha,
            hr.id_usuario,
            u.nombre AS usuario_nombre,
            u.usuario AS usuario_login
        FROM hoja_reporte hr
        LEFT JOIN usuarios u ON u.id_usuario = hr.id_usuario
        WHERE hr.id_reporte = :id_reporte
    """)

    row = db.execute(sql, {"id_reporte": id_reporte}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Hoja de reporte no encontrada")

    # Parsear contenido JSON si existe
    contenido = row["contenido"]
    if contenido and isinstance(contenido, str):
        try:
            contenido = json.loads(contenido)
        except:
            contenido = {}

    hoja_data = {
        "id": row["id_reporte"],
        "id_reporte": row["id_reporte"],
        "id_hoja_reporte": row["id_reporte"],
        "folio": row["folio"],
        "periodo_inicio": row["periodo_inicio"],
        "periodo_fin": row["periodo_fin"],
        "contenido": contenido,
        "archivo": row["archivo"],
        "fecha": row["fecha"],
        "id_usuario": row["id_usuario"],
        "usuario_nombre": row["usuario_nombre"],
        "usuario": row["usuario_login"],
        "mvz": row["usuario_nombre"] or "",
        "upp": "",
        "obs": ""
    }

    return hoja_data


@router.post("")
def crear_hoja_reporte(payload: HojaReporteCreate, db: Session = Depends(get_db)):
    """
    Crea una nueva hoja de reporte
    BD: id_reporte, folio, periodo_inicio, periodo_fin, contenido, archivo, fecha, id_usuario
    """
    try:
        # Convertir contenido a JSON string si es dict
        contenido_json = None
        if payload.contenido:
            contenido_json = json.dumps(payload.contenido)

        insert_sql = text("""
            INSERT INTO hoja_reporte (
                folio,
                periodo_inicio,
                periodo_fin,
                contenido,
                archivo,
                fecha,
                id_usuario
            ) VALUES (
                :folio,
                :periodo_inicio,
                :periodo_fin,
                :contenido,
                :archivo,
                NOW(),
                :id_usuario
            )
        """)

        db.execute(insert_sql, {
            "folio": payload.folio,
            "periodo_inicio": payload.periodo_inicio,
            "periodo_fin": payload.periodo_fin,
            "contenido": contenido_json,
            "archivo": payload.archivo,
            "id_usuario": payload.id_usuario
        })

        new_id = db.execute(text("SELECT LAST_INSERT_ID() AS id")).mappings().first()["id"]
        db.commit()

        return {
            "success": True,
            "message": "Hoja de reporte creada exitosamente",
            "id_reporte": int(new_id),
            "id_hoja_reporte": int(new_id)  # Alias para compatibilidad
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear hoja de reporte: {str(e)}")


@router.put("/{id_reporte}")
def actualizar_hoja_reporte(id_reporte: int, payload: HojaReporteUpdate, db: Session = Depends(get_db)):
    """
    Actualiza una hoja de reporte existente
    BD: id_reporte, folio, periodo_inicio, periodo_fin, contenido, archivo, fecha, id_usuario
    """
    try:
        check_sql = text("SELECT id_reporte FROM hoja_reporte WHERE id_reporte = :id_reporte")
        existe = db.execute(check_sql, {"id_reporte": id_reporte}).first()

        if not existe:
            raise HTTPException(status_code=404, detail="Hoja de reporte no encontrada")

        campos = []
        params = {"id_reporte": id_reporte}

        if payload.folio is not None:
            campos.append("folio = :folio")
            params["folio"] = payload.folio

        if payload.periodo_inicio is not None:
            campos.append("periodo_inicio = :periodo_inicio")
            params["periodo_inicio"] = payload.periodo_inicio

        if payload.periodo_fin is not None:
            campos.append("periodo_fin = :periodo_fin")
            params["periodo_fin"] = payload.periodo_fin

        if payload.contenido is not None:
            campos.append("contenido = :contenido")
            params["contenido"] = json.dumps(payload.contenido)

        if payload.archivo is not None:
            campos.append("archivo = :archivo")
            params["archivo"] = payload.archivo

        if not campos:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        update_sql = f"""
            UPDATE hoja_reporte
            SET {', '.join(campos)}
            WHERE id_reporte = :id_reporte
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


@router.delete("/{id_reporte}")
def eliminar_hoja_reporte(id_reporte: int, db: Session = Depends(get_db)):
    """
    Elimina una hoja de reporte
    BD: PK es id_reporte
    """
    try:
        sql = text("""
            DELETE FROM hoja_reporte
            WHERE id_reporte = :id_reporte
        """)

        result = db.execute(sql, {"id_reporte": id_reporte})
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
