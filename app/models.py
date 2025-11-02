# app/models.py
from datetime import datetime
from sqlmodel import SQLModel, Field

class Sector(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    zona: str | None = None
    activo: bool = True

class Reading(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sector_id: int = Field(index=True)
    ts: datetime = Field(default_factory=datetime.utcnow, index=True)
    inyeccion_m3: float
    consumo_m3: float
    presion_psi: float
    eficiencia: float

class Alert(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sector_id: int = Field(index=True)
    ts: datetime = Field(default_factory=datetime.utcnow, index=True)
    nivel: str  # "alta" | "media" | "baja"
    tipo: str   # "baja_eficiencia" | "sobrepresion" | "no_facturable"
    mensaje: str
    explicacion: str | None = None
    estado: str = "abierta"  # "abierta" | "atendida" | "escalada"
    atendida_por: str | None = None
    atendida_en: datetime | None = None
    escalada_a: str | None = None
    escalada_en: datetime | None = None

class ActionLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    alert_id: int = Field(index=True)
    actor: str
    accion: str  # "ack" | "escalar"
    nota: str | None = None
    ts: datetime = Field(default_factory=datetime.utcnow)