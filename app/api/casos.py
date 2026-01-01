from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from typing import Optional

from app.db.database import get_db

router = APIRouter(prefix="/api/casos", tags=["casos"])


class CasoCreate(BaseModel):
    id_upp: int = Field(..., gt=0)
    fecha_recepcion: date
    observaciones: str | None = None
    id_usuario_crea: int = Field(..., gt=0)  


@router.post("")
def crear_caso(payload: CasoCreate, db: Session = Depends(get_db)):
    try:
        # 1) Generar numero de caso via SP (OUT param)
        db.execute(text("SET @p_numero_caso = ''"))
        db.execute(text("CALL sp_generar_numero_caso(@p_numero_caso)"))
        numero_caso = db.execute(text("SELECT @p_numero_caso AS numero")).mappings().first()["numero"]

        if not numero_caso:
            raise HTTPException(status_code=500, detail="No se pudo generar el número de caso.")

        # 2) Insertar caso
        insert_sql = text("""
            INSERT INTO casos (numero_caso, id_upp, fecha_recepcion, estatus, observaciones, id_usuario_crea)
            VALUES (:numero_caso, :id_upp, :fecha_recepcion, 'ABIERTO', :observaciones, :id_usuario_crea)
        """)
        db.execute(insert_sql, {
            "numero_caso": numero_caso,
            "id_upp": payload.id_upp,
            "fecha_recepcion": payload.fecha_recepcion,
            "observaciones": payload.observaciones,
            "id_usuario_crea": payload.id_usuario_crea,
        })

        # 3) Obtener id del caso insertado
        new_id = db.execute(text("SELECT LAST_INSERT_ID() AS id")).mappings().first()["id"]

        db.commit()

        return {
            "id_caso": int(new_id),
            "numero_caso": numero_caso,
            "estatus": "ABIERTO",
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
    estatus: Optional[str] = None,
    fecha_recepcion: Optional[date] = None,
    folio_hoja_control: Optional[str] = None,
    mvz: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    # casos.estatus es ENUM: ABIERTO, EN_PROCESO, CERRADO, CANCELADO
    sql = """
        SELECT
          c.id_caso,
          c.numero_caso,
          c.fecha_recepcion,
          c.estatus,
          c.observaciones,
          u.id_upp,
          u.clave_upp,
          u.municipio,
          u.localidad,
          p.nombre AS propietario
        FROM casos c
        JOIN upp u ON u.id_upp = c.id_upp
        JOIN propietarios p ON p.id_propietario = u.id_propietario
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

    if estatus:
        sql += " AND c.estatus = :estatus"
        params["estatus"] = estatus.strip().upper()

    if fecha_recepcion:
        sql += " AND c.fecha_recepcion = :fecha_recepcion"
        params["fecha_recepcion"] = fecha_recepcion

    # Dependen de lo que se ingrese como observaciones en el frontend
    if folio_hoja_control:
        sql += " AND (c.observaciones LIKE :folio_hcc)"
        params["folio_hcc"] = f"%{folio_hoja_control.strip()}%"

    if mvz:
        sql += " AND (c.observaciones LIKE :mvz)"
        params["mvz"] = f"%{mvz.strip()}%"

    sql += " ORDER BY c.id_caso DESC LIMIT :limit"

    rows = db.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]
