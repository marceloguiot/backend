# ==================== EMPIEZAN CAMBIOS ====================
# Archivo nuevo: CRUD completo de resultados
# Creado para manejar todas las operaciones de resultados de laboratorio
# ==================== EMPIEZAN CAMBIOS ====================

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import date

from app.db.database import get_db

router = APIRouter(prefix="/api/resultados", tags=["resultados"])


# ==================== EMPIEZAN CAMBIOS ====================
# Modelos Pydantic para resultados
# ==================== EMPIEZAN CAMBIOS ====================

class ResultadoCreate(BaseModel):
    # BD: id_resultado_lab, id_muestra, id_prueba, id_resultado, valor, observaciones, fecha_resultado, id_usuario_valida, created_at
    id_muestra: int
    id_prueba: int
    id_resultado: Optional[int] = None  # FK a cat_resultado (POSITIVO, NEGATIVO, etc.)
    valor: Optional[str] = None
    observaciones: Optional[str] = None
    fecha_resultado: date
    id_usuario_valida: Optional[int] = None

    # Campos del frontend que se mapean
    resultado: Optional[str] = None  # Se puede usar para buscar id_resultado


class ResultadoUpdate(BaseModel):
    # BD: id_resultado_lab, id_muestra, id_prueba, id_resultado, valor, observaciones, fecha_resultado, id_usuario_valida, created_at
    id_prueba: Optional[int] = None
    id_resultado: Optional[int] = None
    valor: Optional[str] = None
    observaciones: Optional[str] = None
    fecha_resultado: Optional[date] = None
    id_usuario_valida: Optional[int] = None

    # Campos del frontend que se mapean
    resultado: Optional[str] = None


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Consultar resultados con filtros
# ==================== EMPIEZAN CAMBIOS ====================

@router.get("")
def consultar_resultados(
    id_muestra: Optional[int] = None,
    id_caso: Optional[int] = None,
    numero_caso: Optional[str] = None,
    id_prueba: Optional[int] = None,
    id_resultado: Optional[int] = None,
    resultado: Optional[str] = None,  # Para compatibilidad con frontend
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Consulta resultados con filtros opcionales
    BD: id_resultado_lab, id_muestra, id_prueba, id_resultado, valor, observaciones, fecha_resultado, id_usuario_valida, created_at
    """
    sql = """
        SELECT
            r.id_resultado_lab,
            r.id_muestra,
            r.id_prueba,
            r.id_resultado,
            r.valor,
            r.observaciones,
            r.fecha_resultado,
            r.id_usuario_valida,
            r.created_at,
            m.codigo_muestra,
            m.id_caso,
            c.numero_caso,
            u.clave_upp,
            p.nombre AS propietario,
            pr.nombre AS prueba_nombre,
            cr.nombre AS resultado_nombre,
            usr_val.nombre AS usuario_valida_nombre,
            tm.descripcion AS tipo_muestra
        FROM resultados r
        INNER JOIN muestras m ON m.id_muestra = r.id_muestra
        INNER JOIN casos c ON c.id_caso = m.id_caso
        INNER JOIN upp u ON u.id_upp = c.id_upp
        INNER JOIN propietarios p ON p.id_propietario = u.id_propietario
        LEFT JOIN cat_prueba pr ON pr.id_prueba = r.id_prueba
        LEFT JOIN cat_resultado cr ON cr.id_resultado = r.id_resultado
        LEFT JOIN usuarios usr_val ON usr_val.id_usuario = r.id_usuario_valida
        LEFT JOIN cat_tipo_muestra tm ON tm.id_tipo_muestra = m.id_tipo_muestra
        WHERE 1=1
    """
    params = {"limit": int(limit)}

    if id_muestra:
        sql += " AND r.id_muestra = :id_muestra"
        params["id_muestra"] = id_muestra

    if id_caso:
        sql += " AND m.id_caso = :id_caso"
        params["id_caso"] = id_caso

    if numero_caso:
        sql += " AND c.numero_caso LIKE :numero_caso"
        params["numero_caso"] = f"%{numero_caso.strip()}%"

    if id_prueba:
        sql += " AND r.id_prueba = :id_prueba"
        params["id_prueba"] = id_prueba

    if id_resultado:
        sql += " AND r.id_resultado = :id_resultado"
        params["id_resultado"] = id_resultado
    elif resultado:
        # Buscar por nombre de resultado para compatibilidad
        sql += " AND cr.nombre = :resultado"
        params["resultado"] = resultado.strip().upper()

    if fecha_desde:
        sql += " AND r.fecha_resultado >= :fecha_desde"
        params["fecha_desde"] = fecha_desde

    if fecha_hasta:
        sql += " AND r.fecha_resultado <= :fecha_hasta"
        params["fecha_hasta"] = fecha_hasta

    sql += " ORDER BY r.id_resultado_lab DESC LIMIT :limit"

    rows = db.execute(text(sql), params).mappings().all()

    # Mapear campos reales de BD a campos esperados por frontend
    resultados_list = []
    for row in rows:
        resultado_data = {
            "id_resultado_lab": row["id_resultado_lab"],
            "id_resultado": row["id_resultado_lab"],  # Alias para frontend
            "id_muestra": row["id_muestra"],
            "codigo_muestra": row["codigo_muestra"],
            "id_prueba": row["id_prueba"],
            "prueba_nombre": row["prueba_nombre"],
            "prueba_realizada": row["prueba_nombre"],  # Alias para frontend
            "id_resultado_cat": row["id_resultado"],  # FK a cat_resultado
            "resultado": row["resultado_nombre"],  # Nombre del resultado (POSITIVO, NEGATIVO, etc.)
            "resultado_nombre": row["resultado_nombre"],
            "valor": row["valor"],
            "observaciones": row["observaciones"],
            "fecha_resultado": row["fecha_resultado"],
            "fecha_analisis": row["fecha_resultado"],  # Alias para frontend
            "id_usuario_valida": row["id_usuario_valida"],
            "usuario_valida": row["usuario_valida_nombre"],
            "created_at": row["created_at"],
            "tipo_muestra": row["tipo_muestra"],
            "id_caso": row["id_caso"],
            "numero_caso": row["numero_caso"],
            "clave_upp": row["clave_upp"],
            "propietario": row["propietario"]
        }
        resultados_list.append(resultado_data)

    return resultados_list


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Obtener resultado por ID
# ==================== EMPIEZAN CAMBIOS ====================

@router.get("/{id_resultado_lab}")
def obtener_resultado(id_resultado_lab: int, db: Session = Depends(get_db)):
    """
    Obtiene un resultado específico por ID
    BD: id_resultado_lab, id_muestra, id_prueba, id_resultado, valor, observaciones, fecha_resultado, id_usuario_valida, created_at
    """
    sql = text("""
        SELECT
            r.id_resultado_lab,
            r.id_muestra,
            r.id_prueba,
            r.id_resultado,
            r.valor,
            r.observaciones,
            r.fecha_resultado,
            r.id_usuario_valida,
            r.created_at,
            m.codigo_muestra,
            m.id_caso,
            c.numero_caso,
            u.clave_upp,
            p.nombre AS propietario,
            pr.nombre AS prueba_nombre,
            cr.nombre AS resultado_nombre,
            usr_val.nombre AS usuario_valida_nombre,
            tm.descripcion AS tipo_muestra
        FROM resultados r
        INNER JOIN muestras m ON m.id_muestra = r.id_muestra
        INNER JOIN casos c ON c.id_caso = m.id_caso
        INNER JOIN upp u ON u.id_upp = c.id_upp
        INNER JOIN propietarios p ON p.id_propietario = u.id_propietario
        LEFT JOIN cat_prueba pr ON pr.id_prueba = r.id_prueba
        LEFT JOIN cat_resultado cr ON cr.id_resultado = r.id_resultado
        LEFT JOIN usuarios usr_val ON usr_val.id_usuario = r.id_usuario_valida
        LEFT JOIN cat_tipo_muestra tm ON tm.id_tipo_muestra = m.id_tipo_muestra
        WHERE r.id_resultado_lab = :id_resultado_lab
    """)

    row = db.execute(sql, {"id_resultado_lab": id_resultado_lab}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")

    resultado_data = {
        "id_resultado_lab": row["id_resultado_lab"],
        "id_resultado": row["id_resultado_lab"],  # Alias para frontend
        "id_muestra": row["id_muestra"],
        "codigo_muestra": row["codigo_muestra"],
        "id_prueba": row["id_prueba"],
        "prueba_nombre": row["prueba_nombre"],
        "prueba_realizada": row["prueba_nombre"],
        "id_resultado_cat": row["id_resultado"],
        "resultado": row["resultado_nombre"],
        "resultado_nombre": row["resultado_nombre"],
        "valor": row["valor"],
        "observaciones": row["observaciones"],
        "fecha_resultado": row["fecha_resultado"],
        "fecha_analisis": row["fecha_resultado"],
        "id_usuario_valida": row["id_usuario_valida"],
        "usuario_valida": row["usuario_valida_nombre"],
        "created_at": row["created_at"],
        "tipo_muestra": row["tipo_muestra"],
        "id_caso": row["id_caso"],
        "numero_caso": row["numero_caso"],
        "clave_upp": row["clave_upp"],
        "propietario": row["propietario"]
    }

    return resultado_data


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Crear nuevo resultado
# ==================== EMPIEZAN CAMBIOS ====================

@router.post("")
def crear_resultado(payload: ResultadoCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo resultado en el sistema
    BD: id_resultado_lab, id_muestra, id_prueba, id_resultado, valor, observaciones, fecha_resultado, id_usuario_valida, created_at
    """
    try:
        # Validar que la muestra existe
        check_muestra = text("""
            SELECT id_muestra FROM muestras WHERE id_muestra = :id_muestra
        """)
        muestra = db.execute(check_muestra, {"id_muestra": payload.id_muestra}).first()

        if not muestra:
            raise HTTPException(status_code=404, detail="La muestra especificada no existe")

        # Determinar id_resultado (puede venir directo o buscarse por nombre)
        id_resultado_cat = payload.id_resultado
        if not id_resultado_cat and payload.resultado:
            res_sql = text("SELECT id_resultado FROM cat_resultado WHERE nombre = :nombre LIMIT 1")
            res_row = db.execute(res_sql, {"nombre": payload.resultado.upper()}).first()
            if res_row:
                id_resultado_cat = res_row[0]

        # Insertar resultado con campos reales de BD
        insert_sql = text("""
            INSERT INTO resultados (
                id_muestra,
                id_prueba,
                id_resultado,
                valor,
                observaciones,
                fecha_resultado,
                id_usuario_valida,
                created_at
            ) VALUES (
                :id_muestra,
                :id_prueba,
                :id_resultado,
                :valor,
                :observaciones,
                :fecha_resultado,
                :id_usuario_valida,
                NOW()
            )
        """)

        db.execute(insert_sql, {
            "id_muestra": payload.id_muestra,
            "id_prueba": payload.id_prueba,
            "id_resultado": id_resultado_cat,
            "valor": payload.valor,
            "observaciones": payload.observaciones,
            "fecha_resultado": payload.fecha_resultado,
            "id_usuario_valida": payload.id_usuario_valida
        })

        new_id = db.execute(text("SELECT LAST_INSERT_ID() AS id")).mappings().first()["id"]
        db.commit()

        return {
            "success": True,
            "message": "Resultado creado exitosamente",
            "id_resultado_lab": int(new_id),
            "id_resultado": int(new_id)  # Alias para frontend
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear resultado: {str(e)}")


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Actualizar resultado
# ==================== EMPIEZAN CAMBIOS ====================

@router.put("/{id_resultado_lab}")
def actualizar_resultado(id_resultado_lab: int, payload: ResultadoUpdate, db: Session = Depends(get_db)):
    """
    Actualiza los datos de un resultado existente
    BD: id_resultado_lab, id_muestra, id_prueba, id_resultado, valor, observaciones, fecha_resultado, id_usuario_valida, created_at
    """
    try:
        check_sql = text("SELECT id_resultado_lab FROM resultados WHERE id_resultado_lab = :id_resultado_lab")
        existe = db.execute(check_sql, {"id_resultado_lab": id_resultado_lab}).first()

        if not existe:
            raise HTTPException(status_code=404, detail="Resultado no encontrado")

        campos = []
        params = {"id_resultado_lab": id_resultado_lab}

        if payload.id_prueba is not None:
            campos.append("id_prueba = :id_prueba")
            params["id_prueba"] = payload.id_prueba

        # Determinar id_resultado
        if payload.id_resultado is not None:
            campos.append("id_resultado = :id_resultado")
            params["id_resultado"] = payload.id_resultado
        elif payload.resultado is not None:
            res_sql = text("SELECT id_resultado FROM cat_resultado WHERE nombre = :nombre LIMIT 1")
            res_row = db.execute(res_sql, {"nombre": payload.resultado.upper()}).first()
            if res_row:
                campos.append("id_resultado = :id_resultado")
                params["id_resultado"] = res_row[0]

        if payload.valor is not None:
            campos.append("valor = :valor")
            params["valor"] = payload.valor

        if payload.observaciones is not None:
            campos.append("observaciones = :observaciones")
            params["observaciones"] = payload.observaciones

        if payload.fecha_resultado is not None:
            campos.append("fecha_resultado = :fecha_resultado")
            params["fecha_resultado"] = payload.fecha_resultado

        if payload.id_usuario_valida is not None:
            campos.append("id_usuario_valida = :id_usuario_valida")
            params["id_usuario_valida"] = payload.id_usuario_valida

        if not campos:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        update_sql = f"""
            UPDATE resultados
            SET {', '.join(campos)}
            WHERE id_resultado_lab = :id_resultado_lab
        """

        db.execute(text(update_sql), params)
        db.commit()

        return {
            "success": True,
            "message": "Resultado actualizado exitosamente"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar resultado: {str(e)}")


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Eliminar resultado
# ==================== EMPIEZAN CAMBIOS ====================

@router.delete("/{id_resultado_lab}")
def eliminar_resultado(id_resultado_lab: int, db: Session = Depends(get_db)):
    """
    Elimina permanentemente un resultado
    BD: PK es id_resultado_lab
    """
    try:
        sql = text("DELETE FROM resultados WHERE id_resultado_lab = :id_resultado_lab")
        result = db.execute(sql, {"id_resultado_lab": id_resultado_lab})
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Resultado no encontrado")

        return {
            "success": True,
            "message": "Resultado eliminado exitosamente"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar resultado: {str(e)}")

# ==================== TERMINAN CAMBIOS ====================
