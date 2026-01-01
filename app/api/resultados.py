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
    id_muestra: int
    prueba_realizada: str
    resultado: str
    fecha_analisis: date
    observaciones: Optional[str] = None
    id_usuario_responsable: Optional[int] = None


class ResultadoUpdate(BaseModel):
    prueba_realizada: Optional[str] = None
    resultado: Optional[str] = None
    fecha_analisis: Optional[date] = None
    observaciones: Optional[str] = None
    id_usuario_responsable: Optional[int] = None


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Consultar resultados con filtros
# ==================== EMPIEZAN CAMBIOS ====================

@router.get("")
def consultar_resultados(
    id_muestra: Optional[int] = None,
    id_caso: Optional[int] = None,
    numero_caso: Optional[str] = None,
    prueba_realizada: Optional[str] = None,
    resultado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Consulta resultados con filtros opcionales
    """
    sql = """
        SELECT
            r.id_resultado,
            r.id_muestra,
            r.prueba_realizada,
            r.resultado,
            r.fecha_analisis,
            r.observaciones,
            r.id_usuario_responsable,
            r.fecha_creacion,
            m.tipo_muestra,
            m.id_caso,
            c.numero_caso,
            u.clave_upp,
            p.nombre AS propietario,
            usr.nombre_usuario AS usuario_responsable
        FROM resultados r
        JOIN muestras m ON m.id_muestra = r.id_muestra
        JOIN casos c ON c.id_caso = m.id_caso
        JOIN upp u ON u.id_upp = c.id_upp
        JOIN propietarios p ON p.id_propietario = u.id_propietario
        LEFT JOIN usuarios usr ON usr.id_usuario = r.id_usuario_responsable
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

    if prueba_realizada:
        sql += " AND r.prueba_realizada LIKE :prueba_realizada"
        params["prueba_realizada"] = f"%{prueba_realizada.strip()}%"

    if resultado:
        sql += " AND r.resultado LIKE :resultado"
        params["resultado"] = f"%{resultado.strip()}%"

    if fecha_desde:
        sql += " AND r.fecha_analisis >= :fecha_desde"
        params["fecha_desde"] = fecha_desde

    if fecha_hasta:
        sql += " AND r.fecha_analisis <= :fecha_hasta"
        params["fecha_hasta"] = fecha_hasta

    sql += " ORDER BY r.id_resultado DESC LIMIT :limit"

    rows = db.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Obtener resultado por ID
# ==================== EMPIEZAN CAMBIOS ====================

@router.get("/{id_resultado}")
def obtener_resultado(id_resultado: int, db: Session = Depends(get_db)):
    """
    Obtiene un resultado específico por ID
    """
    sql = text("""
        SELECT
            r.id_resultado,
            r.id_muestra,
            r.prueba_realizada,
            r.resultado,
            r.fecha_analisis,
            r.observaciones,
            r.id_usuario_responsable,
            r.fecha_creacion,
            m.tipo_muestra,
            m.id_caso,
            c.numero_caso,
            u.clave_upp,
            p.nombre AS propietario,
            usr.nombre_usuario AS usuario_responsable
        FROM resultados r
        JOIN muestras m ON m.id_muestra = r.id_muestra
        JOIN casos c ON c.id_caso = m.id_caso
        JOIN upp u ON u.id_upp = c.id_upp
        JOIN propietarios p ON p.id_propietario = u.id_propietario
        LEFT JOIN usuarios usr ON usr.id_usuario = r.id_usuario_responsable
        WHERE r.id_resultado = :id_resultado
    """)

    row = db.execute(sql, {"id_resultado": id_resultado}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")

    return dict(row)


# ==================== EMPIEZAN CAMBIOS ====================
# Endpoint: Crear nuevo resultado
# ==================== EMPIEZAN CAMBIOS ====================

@router.post("")
def crear_resultado(payload: ResultadoCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo resultado en el sistema
    """
    try:
        # Validar que la muestra existe
        check_muestra = text("""
            SELECT id_muestra FROM muestras WHERE id_muestra = :id_muestra
        """)
        muestra = db.execute(check_muestra, {"id_muestra": payload.id_muestra}).first()

        if not muestra:
            raise HTTPException(status_code=404, detail="La muestra especificada no existe")

        # Validar usuario responsable si se proporciona
        if payload.id_usuario_responsable:
            check_usuario = text("""
                SELECT id_usuario FROM usuarios WHERE id_usuario = :id_usuario
            """)
            usuario = db.execute(check_usuario, {"id_usuario": payload.id_usuario_responsable}).first()

            if not usuario:
                raise HTTPException(status_code=404, detail="El usuario responsable especificado no existe")

        # Insertar resultado
        insert_sql = text("""
            INSERT INTO resultados (
                id_muestra,
                prueba_realizada,
                resultado,
                fecha_analisis,
                observaciones,
                id_usuario_responsable,
                fecha_creacion
            ) VALUES (
                :id_muestra,
                :prueba_realizada,
                :resultado,
                :fecha_analisis,
                :observaciones,
                :id_usuario_responsable,
                NOW()
            )
        """)

        db.execute(insert_sql, {
            "id_muestra": payload.id_muestra,
            "prueba_realizada": payload.prueba_realizada,
            "resultado": payload.resultado,
            "fecha_analisis": payload.fecha_analisis,
            "observaciones": payload.observaciones,
            "id_usuario_responsable": payload.id_usuario_responsable
        })

        new_id = db.execute(text("SELECT LAST_INSERT_ID() AS id")).mappings().first()["id"]
        db.commit()

        return {
            "success": True,
            "message": "Resultado creado exitosamente",
            "id_resultado": int(new_id)
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

@router.put("/{id_resultado}")
def actualizar_resultado(id_resultado: int, payload: ResultadoUpdate, db: Session = Depends(get_db)):
    """
    Actualiza los datos de un resultado existente
    """
    try:
        check_sql = text("SELECT id_resultado FROM resultados WHERE id_resultado = :id_resultado")
        existe = db.execute(check_sql, {"id_resultado": id_resultado}).first()

        if not existe:
            raise HTTPException(status_code=404, detail="Resultado no encontrado")

        campos = []
        params = {"id_resultado": id_resultado}

        if payload.prueba_realizada is not None:
            campos.append("prueba_realizada = :prueba_realizada")
            params["prueba_realizada"] = payload.prueba_realizada

        if payload.resultado is not None:
            campos.append("resultado = :resultado")
            params["resultado"] = payload.resultado

        if payload.fecha_analisis is not None:
            campos.append("fecha_analisis = :fecha_analisis")
            params["fecha_analisis"] = payload.fecha_analisis

        if payload.observaciones is not None:
            campos.append("observaciones = :observaciones")
            params["observaciones"] = payload.observaciones

        if payload.id_usuario_responsable is not None:
            # Validar que el usuario existe
            check_usuario = text("""
                SELECT id_usuario FROM usuarios WHERE id_usuario = :id_usuario
            """)
            usuario = db.execute(check_usuario, {"id_usuario": payload.id_usuario_responsable}).first()

            if not usuario:
                raise HTTPException(status_code=404, detail="El usuario responsable especificado no existe")

            campos.append("id_usuario_responsable = :id_usuario_responsable")
            params["id_usuario_responsable"] = payload.id_usuario_responsable

        if not campos:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        update_sql = f"""
            UPDATE resultados
            SET {', '.join(campos)}
            WHERE id_resultado = :id_resultado
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

@router.delete("/{id_resultado}")
def eliminar_resultado(id_resultado: int, db: Session = Depends(get_db)):
    """
    Elimina permanentemente un resultado
    """
    try:
        sql = text("DELETE FROM resultados WHERE id_resultado = :id_resultado")
        result = db.execute(sql, {"id_resultado": id_resultado})
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
