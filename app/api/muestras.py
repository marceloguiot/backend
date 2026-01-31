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
    # BD: id_muestra, id_caso, id_tipo_muestra, id_estatus_muestra, codigo_muestra, numero_arete, id_especie, id_raza, especie, sexo, edad, fecha_toma, observaciones, created_at, updated_at
    id_caso: int
    codigo_muestra: str
    numero_arete: Optional[str] = None
    id_tipo_muestra: Optional[int] = None
    id_estatus_muestra: Optional[int] = None
    id_especie: Optional[int] = None
    id_raza: Optional[int] = None
    especie: Optional[str] = None  # Campo varchar adicional
    sexo: Optional[str] = None
    edad: Optional[str] = None
    fecha_toma: Optional[date] = None
    observaciones: Optional[str] = None

    # Campos del frontend que se mapean
    tipo_muestra: Optional[str] = None  # Se puede usar para buscar id_tipo_muestra


class MuestraUpdate(BaseModel):
    # BD: id_muestra, id_caso, id_tipo_muestra, id_estatus_muestra, codigo_muestra, numero_arete, id_especie, id_raza, especie, sexo, edad, fecha_toma, observaciones, created_at, updated_at
    codigo_muestra: Optional[str] = None
    numero_arete: Optional[str] = None
    id_tipo_muestra: Optional[int] = None
    id_estatus_muestra: Optional[int] = None
    id_especie: Optional[int] = None
    id_raza: Optional[int] = None
    especie: Optional[str] = None
    sexo: Optional[str] = None
    edad: Optional[str] = None
    fecha_toma: Optional[date] = None
    observaciones: Optional[str] = None

    # Campos del frontend que se mapean
    tipo_muestra: Optional[str] = None


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Consultar muestras con filtros
# ==================== EMPIEZAN CAMBIOS ====================

@router.get("")
def consultar_muestras(
    id_caso: Optional[int] = None,
    codigo_muestra: Optional[str] = None,
    numero_arete: Optional[str] = None,
    id_especie: Optional[int] = None,
    id_tipo_muestra: Optional[int] = None,
    id_estatus_muestra: Optional[int] = None,
    estatus: Optional[str] = None,  # Filtro por nombre de estatus (para compatibilidad con frontend)
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Consulta muestras con filtros opcionales
    BD: id_muestra, id_caso, id_tipo_muestra, id_estatus_muestra, codigo_muestra, numero_arete, id_especie, id_raza, especie, sexo, edad, fecha_toma, observaciones, created_at, updated_at
    """
    sql = """
        SELECT
            m.id_muestra,
            m.id_caso,
            m.codigo_muestra,
            m.numero_arete,
            m.id_tipo_muestra,
            m.id_estatus_muestra,
            m.id_especie,
            m.id_raza,
            m.especie AS especie_texto,
            m.sexo,
            m.edad,
            m.fecha_toma,
            m.observaciones,
            m.created_at,
            m.updated_at,
            c.numero_caso,
            u.clave_upp,
            p.nombre AS nombre_propietario,
            esp.nombre AS especie_cat,
            r.nombre AS raza,
            tm.descripcion AS tipo_muestra,
            em.nombre AS estatus_muestra
        FROM muestras m
        INNER JOIN casos c ON c.id_caso = m.id_caso
        INNER JOIN upp u ON u.id_upp = c.id_upp
        INNER JOIN propietarios p ON p.id_propietario = u.id_propietario
        LEFT JOIN cat_especie esp ON esp.id_especie = m.id_especie
        LEFT JOIN cat_raza r ON r.id_raza = m.id_raza
        LEFT JOIN cat_tipo_muestra tm ON tm.id_tipo_muestra = m.id_tipo_muestra
        LEFT JOIN cat_estatus_muestra em ON em.id_estatus_muestra = m.id_estatus_muestra
        WHERE 1=1
    """
    params = {"limit": int(limit)}

    if id_caso:
        sql += " AND m.id_caso = :id_caso"
        params["id_caso"] = id_caso

    if codigo_muestra:
        sql += " AND m.codigo_muestra LIKE :codigo_muestra"
        params["codigo_muestra"] = f"%{codigo_muestra.strip()}%"

    if numero_arete:
        sql += " AND m.numero_arete LIKE :numero_arete"
        params["numero_arete"] = f"%{numero_arete.strip()}%"

    if id_especie:
        sql += " AND m.id_especie = :id_especie"
        params["id_especie"] = id_especie

    if id_tipo_muestra:
        sql += " AND m.id_tipo_muestra = :id_tipo_muestra"
        params["id_tipo_muestra"] = id_tipo_muestra

    if id_estatus_muestra:
        sql += " AND m.id_estatus_muestra = :id_estatus_muestra"
        params["id_estatus_muestra"] = id_estatus_muestra
    elif estatus:
        # Filtrar por nombre de estatus para compatibilidad con frontend
        sql += " AND em.nombre LIKE :estatus"
        params["estatus"] = f"%{estatus.strip()}%"

    if fecha_desde:
        sql += " AND m.fecha_toma >= :fecha_desde"
        params["fecha_desde"] = fecha_desde

    if fecha_hasta:
        sql += " AND m.fecha_toma <= :fecha_hasta"
        params["fecha_hasta"] = fecha_hasta

    sql += " ORDER BY m.id_muestra DESC LIMIT :limit"

    rows = db.execute(text(sql), params).mappings().all()

    # Mapear campos de BD real a nombres esperados por frontend
    muestras = []
    for row in rows:
        muestra_data = {
            "id_muestra": row["id_muestra"],
            "folio_muestra": row["codigo_muestra"],  # Alias para frontend
            "id_caso": row["id_caso"],
            "numero_caso": row["numero_caso"],
            "codigo_muestra": row["codigo_muestra"],
            "numero_arete": row["numero_arete"],
            "clave_upp": row["clave_upp"],
            "nombre_propietario": row["nombre_propietario"],
            "id_tipo_muestra": row["id_tipo_muestra"],
            "tipo_muestra": row["tipo_muestra"],
            "id_estatus_muestra": row["id_estatus_muestra"],
            "estatus_muestra": row["estatus_muestra"],
            "estatus": row["estatus_muestra"],  # Alias para frontend
            "id_especie": row["id_especie"],
            "id_raza": row["id_raza"],
            "especie": row["especie_cat"] or row["especie_texto"],  # Preferir catálogo
            "especie_texto": row["especie_texto"],
            "raza": row["raza"],
            "sexo": row["sexo"],
            "edad": row["edad"],
            "fecha_toma": row["fecha_toma"],
            "fecha_recepcion": row["created_at"],  # Alias para frontend
            "observaciones": row["observaciones"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
        muestras.append(muestra_data)

    return muestras


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Obtener muestra por ID
# ==================== EMPIEZAN CAMBIOS ====================

@router.get("/{id_muestra}")
def obtener_muestra(id_muestra: int, db: Session = Depends(get_db)):
    """
    Obtiene una muestra específica por ID
    BD: id_muestra, id_caso, id_tipo_muestra, id_estatus_muestra, codigo_muestra, numero_arete, id_especie, id_raza, especie, sexo, edad, fecha_toma, observaciones, created_at, updated_at
    """
    sql = text("""
        SELECT
            m.id_muestra,
            m.id_caso,
            m.codigo_muestra,
            m.numero_arete,
            m.id_tipo_muestra,
            m.id_estatus_muestra,
            m.id_especie,
            m.id_raza,
            m.especie AS especie_texto,
            m.sexo,
            m.edad,
            m.fecha_toma,
            m.observaciones,
            m.created_at,
            m.updated_at,
            c.numero_caso,
            u.clave_upp,
            p.nombre AS nombre_propietario,
            esp.nombre AS especie_cat,
            r.nombre AS raza,
            tm.descripcion AS tipo_muestra,
            em.nombre AS estatus_muestra
        FROM muestras m
        INNER JOIN casos c ON c.id_caso = m.id_caso
        INNER JOIN upp u ON u.id_upp = c.id_upp
        INNER JOIN propietarios p ON p.id_propietario = u.id_propietario
        LEFT JOIN cat_especie esp ON esp.id_especie = m.id_especie
        LEFT JOIN cat_raza r ON r.id_raza = m.id_raza
        LEFT JOIN cat_tipo_muestra tm ON tm.id_tipo_muestra = m.id_tipo_muestra
        LEFT JOIN cat_estatus_muestra em ON em.id_estatus_muestra = m.id_estatus_muestra
        WHERE m.id_muestra = :id_muestra
    """)

    row = db.execute(sql, {"id_muestra": id_muestra}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Muestra no encontrada")

    # Mapear campos de BD real a nombres esperados por frontend
    muestra_data = {
        "id_muestra": row["id_muestra"],
        "folio_muestra": row["codigo_muestra"],
        "id_caso": row["id_caso"],
        "numero_caso": row["numero_caso"],
        "codigo_muestra": row["codigo_muestra"],
        "numero_arete": row["numero_arete"],
        "clave_upp": row["clave_upp"],
        "nombre_propietario": row["nombre_propietario"],
        "id_tipo_muestra": row["id_tipo_muestra"],
        "tipo_muestra": row["tipo_muestra"],
        "id_estatus_muestra": row["id_estatus_muestra"],
        "estatus_muestra": row["estatus_muestra"],
        "estatus": row["estatus_muestra"],
        "id_especie": row["id_especie"],
        "id_raza": row["id_raza"],
        "especie": row["especie_cat"] or row["especie_texto"],
        "especie_texto": row["especie_texto"],
        "raza": row["raza"],
        "sexo": row["sexo"],
        "edad": row["edad"],
        "fecha_toma": row["fecha_toma"],
        "fecha_recepcion": row["created_at"],
        "observaciones": row["observaciones"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }

    return muestra_data


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Crear nueva muestra
# ==================== EMPIEZAN CAMBIOS ====================

@router.post("")
def crear_muestra(payload: MuestraCreate, db: Session = Depends(get_db)):
    """
    Crea una nueva muestra en el sistema
    BD: id_muestra, id_caso, id_tipo_muestra, id_estatus_muestra, codigo_muestra, numero_arete, id_especie, id_raza, especie, sexo, edad, fecha_toma, observaciones, created_at, updated_at
    """
    try:
        # Validar que el caso existe
        check_caso = text("""
            SELECT id_caso FROM casos WHERE id_caso = :id_caso
        """)
        caso = db.execute(check_caso, {"id_caso": payload.id_caso}).first()

        if not caso:
            raise HTTPException(status_code=404, detail="El caso especificado no existe")

        # Determinar id_tipo_muestra (puede venir directo o buscarse por nombre)
        id_tipo_muestra = payload.id_tipo_muestra
        if not id_tipo_muestra and payload.tipo_muestra:
            tipo_sql = text("SELECT id_tipo_muestra FROM cat_tipo_muestra WHERE descripcion LIKE :desc LIMIT 1")
            tipo_row = db.execute(tipo_sql, {"desc": f"%{payload.tipo_muestra}%"}).first()
            if tipo_row:
                id_tipo_muestra = tipo_row[0]

        # Si no se proporciona id_estatus_muestra, buscar el estatus por defecto (ej: PENDIENTE)
        id_estatus_muestra = payload.id_estatus_muestra
        if not id_estatus_muestra:
            estatus_sql = text("SELECT id_estatus_muestra FROM cat_estatus_muestra WHERE nombre = 'PENDIENTE' LIMIT 1")
            estatus_row = db.execute(estatus_sql).first()
            if estatus_row:
                id_estatus_muestra = estatus_row[0]

        # Insertar muestra con campos reales de BD
        insert_sql = text("""
            INSERT INTO muestras (
                id_caso,
                id_tipo_muestra,
                id_estatus_muestra,
                codigo_muestra,
                numero_arete,
                id_especie,
                id_raza,
                especie,
                sexo,
                edad,
                fecha_toma,
                observaciones,
                created_at
            ) VALUES (
                :id_caso,
                :id_tipo_muestra,
                :id_estatus_muestra,
                :codigo_muestra,
                :numero_arete,
                :id_especie,
                :id_raza,
                :especie,
                :sexo,
                :edad,
                :fecha_toma,
                :observaciones,
                NOW()
            )
        """)

        db.execute(insert_sql, {
            "id_caso": payload.id_caso,
            "id_tipo_muestra": id_tipo_muestra,
            "id_estatus_muestra": id_estatus_muestra,
            "codigo_muestra": payload.codigo_muestra,
            "numero_arete": payload.numero_arete,
            "id_especie": payload.id_especie,
            "id_raza": payload.id_raza,
            "especie": payload.especie,
            "sexo": payload.sexo,
            "edad": payload.edad,
            "fecha_toma": payload.fecha_toma,
            "observaciones": payload.observaciones
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
    BD: id_muestra, id_caso, id_tipo_muestra, id_estatus_muestra, codigo_muestra, numero_arete, id_especie, id_raza, especie, sexo, edad, fecha_toma, observaciones, created_at, updated_at
    """
    try:
        check_sql = text("SELECT id_muestra FROM muestras WHERE id_muestra = :id_muestra")
        existe = db.execute(check_sql, {"id_muestra": id_muestra}).first()

        if not existe:
            raise HTTPException(status_code=404, detail="Muestra no encontrada")

        campos = []
        params = {"id_muestra": id_muestra}

        if payload.codigo_muestra is not None:
            campos.append("codigo_muestra = :codigo_muestra")
            params["codigo_muestra"] = payload.codigo_muestra

        if payload.numero_arete is not None:
            campos.append("numero_arete = :numero_arete")
            params["numero_arete"] = payload.numero_arete

        # Determinar id_tipo_muestra
        if payload.id_tipo_muestra is not None:
            campos.append("id_tipo_muestra = :id_tipo_muestra")
            params["id_tipo_muestra"] = payload.id_tipo_muestra
        elif payload.tipo_muestra is not None:
            tipo_sql = text("SELECT id_tipo_muestra FROM cat_tipo_muestra WHERE descripcion LIKE :desc LIMIT 1")
            tipo_row = db.execute(tipo_sql, {"desc": f"%{payload.tipo_muestra}%"}).first()
            if tipo_row:
                campos.append("id_tipo_muestra = :id_tipo_muestra")
                params["id_tipo_muestra"] = tipo_row[0]

        if payload.id_estatus_muestra is not None:
            campos.append("id_estatus_muestra = :id_estatus_muestra")
            params["id_estatus_muestra"] = payload.id_estatus_muestra

        if payload.id_especie is not None:
            campos.append("id_especie = :id_especie")
            params["id_especie"] = payload.id_especie

        if payload.id_raza is not None:
            campos.append("id_raza = :id_raza")
            params["id_raza"] = payload.id_raza

        if payload.especie is not None:
            campos.append("especie = :especie")
            params["especie"] = payload.especie

        if payload.sexo is not None:
            campos.append("sexo = :sexo")
            params["sexo"] = payload.sexo

        if payload.edad is not None:
            campos.append("edad = :edad")
            params["edad"] = payload.edad

        if payload.fecha_toma is not None:
            campos.append("fecha_toma = :fecha_toma")
            params["fecha_toma"] = payload.fecha_toma

        if payload.observaciones is not None:
            campos.append("observaciones = :observaciones")
            params["observaciones"] = payload.observaciones

        if not campos:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        # Agregar updated_at
        campos.append("updated_at = NOW()")

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
