# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from .db import init_db
from .routers.sim import router as sim_router
from .services.sim import iniciar_simulacion_segundo_plano, detener_simulacion_segundo_plano


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida de la aplicación.

    Al iniciar:
      - Inicializa la base de datos (tablas si no existen).
      - Arranca la simulación en segundo plano (genera lecturas y alertas sintéticas).

    Al apagar:
      - Detiene la simulación en segundo plano limpiamente.
    """
    init_db()
    await iniciar_simulacion_segundo_plano()
    try:
        yield
    finally:
        await detener_simulacion_segundo_plano()


app = FastAPI(title="SAPAL Dashboard API", version="0.1.0", lifespan=lifespan)

# CORS abierto para demo; en producción limita dominios.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root():
    """Redirige a la documentación interactiva de FastAPI."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Salud"])
async def health_check():
    """
    Verificación rápida de salud del servicio.
    Devuelve 'healthy' si la API está lista.
    """
    mensaje = "Dashboard de SAPAL 💧 funcionando correctamente. 🚀"
    return {"status": "healthy", "message": mensaje}


# Rutas principales de la simulación / tablero
app.include_router(sim_router, prefix="/sim", tags=["Simulacion"])