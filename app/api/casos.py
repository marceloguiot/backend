from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from typing import Optional

from app.db.database import get_db

router = APIRouter(prefix="/api/casos", tags=["casos"])


class CasoCreate(BaseModel):
    # BD: id_caso, numero_caso, id_upp, id_mvz, id_usuario_recepciona, id_estatus_caso, fecha_recepcion, semana_epidemiologica, anio_epidemiologico, observaciones, created_at, updated_at
    id_upp: int = Field(..., gt=0)
    id_mvz: Optional[int] = None
    id_usuario_recepciona: Optional[int] = None
    id_estatus_caso: Optional[int] = None
    fecha_recepcion: date
    semana_epidemiologica: Optional[int] = None
    anio_epidemiologico: Optional[int] = None
    observaciones: str | None = None
    id_usuario_crea: int = Field(..., gt=0)  # Se mapea a id_usuario_recepciona si no viene  


@router.post("")
def crear_caso(payload: CasoCreate, db: Session = Depends(get_db)):
    """
    BD: id_caso, numero_caso, id_upp, id_mvz, id_usuario_recepciona, id_estatus_caso, fecha_recepcion, semana_epidemiologica, anio_epidemiologico, observaciones, created_at, updated_at
    """
    try:
        # 1) Generar numero de caso via SP (OUT param)
        db.execute(text("SET @p_numero_caso = ''"))
        db.execute(text("CALL sp_generar_numero_caso(@p_numero_caso)"))
        numero_caso = db.execute(text("SELECT @p_numero_caso AS numero")).mappings().first()["numero"]

        if not numero_caso:
            raise HTTPException(status_code=500, detail="No se pudo generar el número de caso.")

        # Determinar id_estatus_caso (buscar ABIERTO por defecto)
        id_estatus_caso = payload.id_estatus_caso
        if not id_estatus_caso:
            estatus_sql = text("SELECT id_estatus_caso FROM cat_estatus_caso WHERE nombre = 'ABIERTO' LIMIT 1")
            estatus_row = db.execute(estatus_sql).first()
            if estatus_row:
                id_estatus_caso = estatus_row[0]

        # Determinar id_usuario_recepciona
        id_usuario_recepciona = payload.id_usuario_recepciona or payload.id_usuario_crea

        # Calcular semana y año epidemiológico si no vienen
        semana_epi = payload.semana_epidemiologica
        anio_epi = payload.anio_epidemiologico
        if not semana_epi or not anio_epi:
            # Calcular basado en fecha_recepcion
            from datetime import datetime
            fecha = payload.fecha_recepcion
            anio_epi = anio_epi or fecha.year
            # Semana ISO
            semana_epi = semana_epi or fecha.isocalendar()[1]

        # 2) Insertar caso con campos reales de BD
        insert_sql = text("""
            INSERT INTO casos (
                numero_caso,
                id_upp,
                id_mvz,
                id_usuario_recepciona,
                id_estatus_caso,
                fecha_recepcion,
                semana_epidemiologica,
                anio_epidemiologico,
                observaciones,
                created_at
            ) VALUES (
                :numero_caso,
                :id_upp,
                :id_mvz,
                :id_usuario_recepciona,
                :id_estatus_caso,
                :fecha_recepcion,
                :semana_epidemiologica,
                :anio_epidemiologico,
                :observaciones,
                NOW()
            )
        """)
        db.execute(insert_sql, {
            "numero_caso": numero_caso,
            "id_upp": payload.id_upp,
            "id_mvz": payload.id_mvz,
            "id_usuario_recepciona": id_usuario_recepciona,
            "id_estatus_caso": id_estatus_caso,
            "fecha_recepcion": payload.fecha_recepcion,
            "semana_epidemiologica": semana_epi,
            "anio_epidemiologico": anio_epi,
            "observaciones": payload.observaciones,
        })

        # 3) Obtener id del caso insertado
        new_id = db.execute(text("SELECT LAST_INSERT_ID() AS id")).mappings().first()["id"]

        db.commit()

        return {
            "id_caso": int(new_id),
            "numero_caso": numero_caso,
            "id_estatus_caso": id_estatus_caso,
            "estatus": "ABIERTO",  # Para compatibilidad con frontend
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))



@router.get("")
def consultar_casos(
    numero_caso: Optional[str] = None,
    id_upp: Optional[int] = None,
    clave_upp: Optional[str] = None,
    propietario: Optional[str] = None,
    id_estatus_caso: Optional[int] = None,
    estatus: Optional[str] = None,  # Para compatibilidad con frontend
    fecha_recepcion: Optional[date] = None,
    id_mvz: Optional[int] = None,
    mvz: Optional[str] = None,
    semana_epidemiologica: Optional[int] = None,
    anio_epidemiologico: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    BD: id_caso, numero_caso, id_upp, id_mvz, id_usuario_recepciona, id_estatus_caso, fecha_recepcion, semana_epidemiologica, anio_epidemiologico, observaciones, created_at, updated_at
    """
    sql = """
        SELECT
          c.id_caso,
          c.numero_caso,
          c.id_upp,
          c.id_mvz,
          c.id_usuario_recepciona,
          c.id_estatus_caso,
          c.fecha_recepcion,
          c.semana_epidemiologica,
          c.anio_epidemiologico,
          c.observaciones,
          c.created_at,
          c.updated_at,
          u.clave_upp,
          m.nombre AS municipio_nombre,
          u.localidad,
          p.nombre AS propietario,
          ec.nombre AS estatus_caso,
          mvz_user.nombre AS mvz_nombre,
          rec_user.nombre AS usuario_recepciona_nombre
        FROM casos c
        JOIN upp u ON u.id_upp = c.id_upp
        JOIN propietarios p ON p.id_propietario = u.id_propietario
        LEFT JOIN cat_municipio m ON m.id_municipio = u.id_municipio
        LEFT JOIN cat_estatus_caso ec ON ec.id_estatus_caso = c.id_estatus_caso
        LEFT JOIN mvz ON mvz.id_mvz = c.id_mvz
        LEFT JOIN usuarios mvz_user ON mvz_user.id_usuario = c.id_mvz
        LEFT JOIN usuarios rec_user ON rec_user.id_usuario = c.id_usuario_recepciona
        WHERE 1=1
    """
    params = {"limit": int(limit)}

    if numero_caso:
        sql += " AND c.numero_caso LIKE :numero_caso"
        params["numero_caso"] = f"%{numero_caso.strip()}%"

    if id_upp:
        sql += " AND c.id_upp = :id_upp"
        params["id_upp"] = int(id_upp)

    if clave_upp:
        sql += " AND u.clave_upp LIKE :clave_upp"
        params["clave_upp"] = f"%{clave_upp.strip()}%"

    if propietario:
        sql += " AND p.nombre LIKE :propietario"
        params["propietario"] = f"%{propietario.strip()}%"

    if id_estatus_caso:
        sql += " AND c.id_estatus_caso = :id_estatus_caso"
        params["id_estatus_caso"] = id_estatus_caso
    elif estatus:
        # Buscar por nombre de estatus para compatibilidad
        sql += " AND ec.nombre = :estatus"
        params["estatus"] = estatus.strip().upper()

    if fecha_recepcion:
        sql += " AND c.fecha_recepcion = :fecha_recepcion"
        params["fecha_recepcion"] = fecha_recepcion

    if id_mvz:
        sql += " AND c.id_mvz = :id_mvz"
        params["id_mvz"] = id_mvz
    elif mvz:
        sql += " AND (mvz.nombre LIKE :mvz OR mvz_user.nombre LIKE :mvz)"
        params["mvz"] = f"%{mvz.strip()}%"

    if semana_epidemiologica:
        sql += " AND c.semana_epidemiologica = :semana_epidemiologica"
        params["semana_epidemiologica"] = semana_epidemiologica

    if anio_epidemiologico:
        sql += " AND c.anio_epidemiologico = :anio_epidemiologico"
        params["anio_epidemiologico"] = anio_epidemiologico

    sql += " ORDER BY c.id_caso DESC LIMIT :limit"

    rows = db.execute(text(sql), params).mappings().all()

    # Mapear a formato esperado por frontend
    casos = []
    for row in rows:
        caso_data = {
            "id_caso": row["id_caso"],
            "numero_caso": row["numero_caso"],
            "id_upp": row["id_upp"],
            "clave_upp": row["clave_upp"],
            "id_mvz": row["id_mvz"],
            "mvz": row["mvz_nombre"],
            "id_usuario_recepciona": row["id_usuario_recepciona"],
            "usuario_recepciona": row["usuario_recepciona_nombre"],
            "id_estatus_caso": row["id_estatus_caso"],
            "estatus_caso": row["estatus_caso"],
            "estatus": row["estatus_caso"],  # Alias para frontend
            "fecha_recepcion": row["fecha_recepcion"],
            "semana_epidemiologica": row["semana_epidemiologica"],
            "anio_epidemiologico": row["anio_epidemiologico"],
            "observaciones": row["observaciones"],
            "municipio": row["municipio_nombre"],
            "localidad": row["localidad"],
            "propietario": row["propietario"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
        casos.append(caso_data)

    return casos
