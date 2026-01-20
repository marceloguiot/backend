from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from app.db.database import test_db_connection
from app.api.casos import router as casos_router
from app.api.upp import router as upp_router
from app.api.propietarios import router as propietarios_router
from app.api.auth import router as auth_router
from app.api.usuarios import router as usuarios_router
from app.api.muestras import router as muestras_router
from app.api.resultados import router as resultados_router
from app.api.hoja_reporte import router as hoja_reporte_router



app = FastAPI(title="SISTPEC API")


app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(casos_router)
app.include_router(upp_router)
app.include_router(propietarios_router)
app.include_router(muestras_router)
app.include_router(resultados_router)
app.include_router(hoja_reporte_router)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dictamenes-five.vercel.app/","*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "SISTPEC API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db-ping")
def db_ping():
    try:
        test_db_connection()
        return {"db": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))