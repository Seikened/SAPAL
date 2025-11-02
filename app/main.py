from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from .db import init_db
from .routers.sim import router as sim_router
from .services.sim import start_background_simulation, stop_background_simulation


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Se ejecuta al iniciar y cerrar la app."""
    init_db()
    await start_background_simulation()
    try:
        yield
    finally:
        await stop_background_simulation()


app = FastAPI(title="SAPAL Dashboard API", version="0.1.0", lifespan=lifespan)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Puedes limitar a dominios específicos si quieres
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"])
async def health_check():
    """Ruta simple para verificar que el servicio esté vivo."""
    mensaje = "Dashboard de SAPAL 💧 funcionando correctamente. 🚀"
    return {"status": "healthy", "message": mensaje}


# Registrar el router principal
app.include_router(sim_router, prefix="/sim", tags=["Simulacion"])