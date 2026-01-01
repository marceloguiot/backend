# ==================== EMPIEZAN CAMBIOS ====================
# Archivo nuevo: CRUD completo de muestras
# Creado para manejar todas las operaciones de muestras
# ==================== EMPIEZAN CAMBIOS ====================

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import date

from app.db.database import get_db

router = APIRouter(prefix="/api/muestras", tags=["muestras"])


# ==================== EMPIEZAN CAMBIOS ====================
# Modelos Pydantic para muestras
# ==================== EMPIEZAN CAMBIOS ====================

class MuestraCreate(BaseModel):
    id_caso: int
    tipo_muestra: str
    cantidad: Optional[int] = 1
    fecha_toma: date
    observaciones: Optional[str] = None
    estatus: str = "PENDIENTE"  # PENDIENTE, EN_PROCESO, COMPLETADO, RECHAZADO


class MuestraUpdate(BaseModel):
    tipo_muestra: Optional[str] = None
    cantidad: Optional[int] = None
    fecha_toma: Optional[date] = None
    observaciones: Optional[str] = None
    estatus: Optional[str] = None


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Consultar muestras con filtros
# ==================== EMPIEZAN CAMBIOS ====================

@router.get("")
def consultar_muestras(
    id_caso: Optional[int] = None,
    numero_caso: Optional[str] = None,
    tipo_muestra: Optional[str] = None,
    estatus: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Consulta muestras con filtros opcionales
    """
    sql = """
        SELECT
            m.id_muestra,
            m.id_caso,
            m.tipo_muestra,
            m.cantidad,
            m.fecha_toma,
            m.observaciones,
            m.estatus,
            m.fecha_creacion,
            c.numero_caso,
            u.clave_upp,
            p.nombre AS propietario
        FROM muestras m
        JOIN casos c ON c.id_caso = m.id_caso
        JOIN upp u ON u.id_upp = c.id_upp
        JOIN propietarios p ON p.id_propietario = u.id_propietario
        WHERE 1=1
    """
    params = {"limit": int(limit)}

    if id_caso:
        sql += " AND m.id_caso = :id_caso"
        params["id_caso"] = id_caso

    if numero_caso:
        sql += " AND c.numero_caso LIKE :numero_caso"
        params["numero_caso"] = f"%{numero_caso.strip()}%"

    if tipo_muestra:
        sql += " AND m.tipo_muestra LIKE :tipo_muestra"
        params["tipo_muestra"] = f"%{tipo_muestra.strip()}%"

    if estatus:
        sql += " AND m.estatus = :estatus"
        params["estatus"] = estatus.strip().upper()

    if fecha_desde:
        sql += " AND m.fecha_toma >= :fecha_desde"
        params["fecha_desde"] = fecha_desde

    if fecha_hasta:
        sql += " AND m.fecha_toma <= :fecha_hasta"
        params["fecha_hasta"] = fecha_hasta

    sql += " ORDER BY m.id_muestra DESC LIMIT :limit"

    rows = db.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Obtener muestra por ID
# ==================== EMPIEZAN CAMBIOS ====================

@router.get("/{id_muestra}")
def obtener_muestra(id_muestra: int, db: Session = Depends(get_db)):
    """
    Obtiene una muestra específica por ID
    """
    sql = text("""
        SELECT
            m.id_muestra,
            m.id_caso,
            m.tipo_muestra,
            m.cantidad,
            m.fecha_toma,
            m.observaciones,
            m.estatus,
            m.fecha_creacion,
            c.numero_caso,
            u.clave_upp,
            p.nombre AS propietario
        FROM muestras m
        JOIN casos c ON c.id_caso = m.id_caso
        JOIN upp u ON u.id_upp = c.id_upp
        JOIN propietarios p ON p.id_propietario = u.id_propietario
        WHERE m.id_muestra = :id_muestra
    """)

    row = db.execute(sql, {"id_muestra": id_muestra}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Muestra no encontrada")

    return dict(row)


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Crear nueva muestra
# ==================== EMPIEZAN CAMBIOS ====================

@router.post("")
def crear_muestra(payload: MuestraCreate, db: Session = Depends(get_db)):
    """
    Crea una nueva muestra en el sistema
    """
    try:
        # Validar que el caso existe
        check_caso = text("""
            SELECT id_caso FROM casos WHERE id_caso = :id_caso
        """)
        caso = db.execute(check_caso, {"id_caso": payload.id_caso}).first()

        if not caso:
            raise HTTPException(status_code=404, detail="El caso especificado no existe")

        # Insertar muestra
        insert_sql = text("""
            INSERT INTO muestras (
                id_caso,
                tipo_muestra,
                cantidad,
                fecha_toma,
                observaciones,
                estatus,
                fecha_creacion
            ) VALUES (
                :id_caso,
                :tipo_muestra,
                :cantidad,
                :fecha_toma,
                :observaciones,
                :estatus,
                NOW()
            )
        """)

        db.execute(insert_sql, {
            "id_caso": payload.id_caso,
            "tipo_muestra": payload.tipo_muestra,
            "cantidad": payload.cantidad,
            "fecha_toma": payload.fecha_toma,
            "observaciones": payload.observaciones,
            "estatus": payload.estatus.upper()
        })

        new_id = db.execute(text("SELECT LAST_INSERT_ID() AS id")).mappings().first()["id"]
        db.commit()

        return {
            "success": True,
            "message": "Muestra creada exitosamente",
            "id_muestra": int(new_id)
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear muestra: {str(e)}")


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Actualizar muestra
# ==================== EMPIEZAN CAMBIOS ====================

@router.put("/{id_muestra}")
def actualizar_muestra(id_muestra: int, payload: MuestraUpdate, db: Session = Depends(get_db)):
    """
    Actualiza los datos de una muestra existente
    """
    try:
        check_sql = text("SELECT id_muestra FROM muestras WHERE id_muestra = :id_muestra")
        existe = db.execute(check_sql, {"id_muestra": id_muestra}).first()

        if not existe:
            raise HTTPException(status_code=404, detail="Muestra no encontrada")

        campos = []
        params = {"id_muestra": id_muestra}

        if payload.tipo_muestra is not None:
            campos.append("tipo_muestra = :tipo_muestra")
            params["tipo_muestra"] = payload.tipo_muestra

        if payload.cantidad is not None:
            campos.append("cantidad = :cantidad")
            params["cantidad"] = payload.cantidad

        if payload.fecha_toma is not None:
            campos.append("fecha_toma = :fecha_toma")
            params["fecha_toma"] = payload.fecha_toma

        if payload.observaciones is not None:
            campos.append("observaciones = :observaciones")
            params["observaciones"] = payload.observaciones

        if payload.estatus is not None:
            campos.append("estatus = :estatus")
            params["estatus"] = payload.estatus.upper()

        if not campos:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        update_sql = f"""
            UPDATE muestras
            SET {', '.join(campos)}
            WHERE id_muestra = :id_muestra
        """

        db.execute(text(update_sql), params)
        db.commit()

        return {
            "success": True,
            "message": "Muestra actualizada exitosamente"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar muestra: {str(e)}")


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Eliminar muestra
# ==================== EMPIEZAN CAMBIOS ====================

@router.delete("/{id_muestra}")
def eliminar_muestra(id_muestra: int, db: Session = Depends(get_db)):
    """
    Elimina permanentemente una muestra
    """
    try:
        sql = text("DELETE FROM muestras WHERE id_muestra = :id_muestra")
        result = db.execute(sql, {"id_muestra": id_muestra})
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Muestra no encontrada")

        return {
            "success": True,
            "message": "Muestra eliminada exitosamente"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar muestra: {str(e)}")

# ==================== TERMINAN CAMBIOS ====================
