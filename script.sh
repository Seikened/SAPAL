#!/usr/bin/env bash
# bootstrap_fastapi.sh — FastAPI + SQLModel + SQLite, modular y listo para correr.
# Uso:
#   chmod +x bootstrap_fastapi.sh
#   ./bootstrap_fastapi.sh
set -euo pipefail

echo "▶️  Preparando estructura..."
mkdir -p app/routers app/services

touch app/__init__.py app/routers/__init__.py

echo "▶️  Escribiendo archivos base..."

# --- app/main.py ---
cat > app/main.py <<'PY'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import init_db
from .routers.items import router as items_router

app = FastAPI(title="SAPAL Proto API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(items_router, prefix="/items", tags=["items"])
PY

# --- app/db.py ---
cat > app/db.py <<'PY'
from sqlmodel import SQLModel, create_engine, Session

ENGINE = create_engine("sqlite:///./app.db", echo=False)

def init_db():
    SQLModel.metadata.create_all(ENGINE)

def get_session():
    with Session(ENGINE) as session:
        yield session
PY

# --- app/models.py ---
cat > app/models.py <<'PY'
from datetime import datetime
from sqlmodel import SQLModel, Field

class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
PY

# --- app/schemas.py ---
cat > app/schemas.py <<'PY'
from datetime import datetime
from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str
    description: str | None = None

class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class ItemRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime
PY

# --- app/services/items.py ---
cat > app/services/items.py <<'PY'
from sqlmodel import Session, select
from fastapi import HTTPException
from ..models import Item
from ..schemas import ItemCreate, ItemUpdate

def create_item(session: Session, data: ItemCreate) -> Item:
    obj = Item(name=data.name, description=data.description)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj

def list_items(session: Session, limit: int, offset: int) -> list[Item]:
    return session.exec(select(Item).offset(offset).limit(limit)).all()

def get_item(session: Session, item_id: int) -> Item:
    obj = session.get(Item, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Item not found")
    return obj

def update_item(session: Session, item_id: int, data: ItemUpdate) -> Item:
    obj = session.get(Item, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Item not found")
    if data.name is not None:
        obj.name = data.name
    if data.description is not None:
        obj.description = data.description
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj

def delete_item(session: Session, item_id: int) -> None:
    obj = session.get(Item, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Item not found")
    session.delete(obj)
    session.commit()
PY

# --- app/routers/items.py ---
cat > app/routers/items.py <<'PY'
from fastapi import APIRouter, Depends
from sqlmodel import Session
from ..db import get_session
from ..schemas import ItemCreate, ItemUpdate, ItemRead
from ..services import items as svc

router = APIRouter()

@router.post("", response_model=ItemRead)
def create(payload: ItemCreate, session: Session = Depends(get_session)):
    return svc.create_item(session, payload)

@router.get("", response_model=list[ItemRead])
def list_(limit: int = 10, offset: int = 0, session: Session = Depends(get_session)):
    return svc.list_items(session, limit, offset)

@router.get("/{item_id}", response_model=ItemRead)
def retrieve(item_id: int, session: Session = Depends(get_session)):
    return svc.get_item(session, item_id)

@router.put("/{item_id}", response_model=ItemRead)
def update(item_id: int, payload: ItemUpdate, session: Session = Depends(get_session)):
    return svc.update_item(session, item_id, payload)

@router.delete("/{item_id}", status_code=204)
def delete(item_id: int, session: Session = Depends(get_session)):
    svc.delete_item(session, item_id)
PY

# --- READMEs para orientación rápida ---
cat > app/README.md <<'MD'
# app/
**Qué va aquí:** inicialización de la app, middlewares, montaje de routers y puntos de entrada.
**Archivo clave:** `main.py` crea `FastAPI`, configura CORS y registra routers. `db.py` inicializa SQLite y la sesión.
MD

cat > app/routers/README.md <<'MD'
# app/routers/
**Qué va aquí:** endpoints agrupados por dominio usando `APIRouter`.
**Cómo usar:** crea `foo.py` con `router = APIRouter()` y define rutas; en `app/main.py` haz `include_router(foo.router, prefix="/foo", tags=["foo"])`.
**Ejemplo:** `items.py` expone CRUD de /items.
MD

cat > app/services/README.md <<'MD'
# app/services/
**Qué va aquí:** lógica de negocio reutilizable, sin detalles de HTTP.
**Ventaja:** testear servicios sin levantar FastAPI.
**Ejemplo:** `items.py` contiene create/list/get/update/delete sobre `Item`.
MD

# --- .gitignore básico ---
if [ ! -f .gitignore ]; then
cat > .gitignore <<'GI'
__pycache__/
*.pyc
*.pyo
*.DS_Store
.venv/
app.db
GI
fi

# --- pyproject mínimo si no existe ---
if [ ! -f pyproject.toml ]; then
cat > pyproject.toml <<'TOML'
[project]
name = "sapal-proto"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[tool.uv]
# uv gestionará deps en uv.lock
TOML
fi

# --- Dependencias con uv ---
if ! command -v uv >/dev/null 2>&1; then
  echo "❌ No encontré 'uv'. Instálalo primero (brew install uv) o usa pip."
  exit 1
fi

echo "▶️  Instalando dependencias con uv..."
uv add "fastapi[all]" sqlmodel uvicorn

# --- Runner cómodo ---
cat > run_dev.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
uv run uvicorn app.main:app --reload --port 8000
SH
chmod +x run_dev.sh

echo "✅ Listo. Arranca con: ./run_dev.sh"
echo "➡️  Docs: http://127.0.0.1:8000/docs"
echo "➡️  Salud: curl http://127.0.0.1:8000/health"
echo "➡️  Crear item: curl -X POST http://127.0.0.1:8000/items -H 'Content-Type: application/json' -d '{\"name\":\"Test\",\"description\":\"hola\"}'"