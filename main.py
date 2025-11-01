# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, Session, create_engine, select
from datetime import datetime

# --- Configuración base ---
app = FastAPI(title="Proto API", version="0.1.0")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # por si usas Vite
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Modelo y DB ---
class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

engine = create_engine("sqlite:///./app.db", echo=False)

# Crear tablas al iniciar
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

# --- Dependencia de sesión ---
def get_session():
    with Session(engine) as session:
        yield session

# --- Endpoints ---
@app.get("/health")
def health_check():
    return {"ok": True, "message": "API is healthy 🚀"}

@app.post("/items")
def create_item(item: Item, session: Session = Depends(get_session)):
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@app.get("/items")
def read_items(limit: int = 10, offset: int = 0, session: Session = Depends(get_session)):
    items = session.exec(select(Item).offset(offset).limit(limit)).all()
    return items

@app.get("/items/{item_id}")
def read_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/items/{item_id}")
def update_item(item_id: int, updated: Item, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.name = updated.name
    item.description = updated.description
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    session.delete(item)
    session.commit()