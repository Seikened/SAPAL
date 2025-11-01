# app/routers/
**Qué va aquí:** endpoints agrupados por dominio usando `APIRouter`.
**Cómo usar:** crea `foo.py` con `router = APIRouter()` y define rutas; en `app/main.py` haz `include_router(foo.router, prefix="/foo", tags=["foo"])`.
**Ejemplo:** `items.py` expone CRUD de /items.
