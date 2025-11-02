# app/schemas.py
from datetime import datetime
from pydantic import BaseModel
from typing import List, Literal

class KPIResponse(BaseModel):
    ts: datetime
    eficiencia: float
    tiempo_decision_min: int
    uso_datos_pct: float
    sectores_en_riesgo: int

class SectorCard(BaseModel):
    id: int
    nombre: str
    estado: Literal["normal", "alerta", "critico"]
    eficiencia: float
    presion_psi: float
    alertas_abiertas: int
    tendencia: list[float]

class SectorsResponse(BaseModel):
    items: List[SectorCard]

class AlertRead(BaseModel):
    id: int
    nivel: Literal["alta", "media", "baja"]
    titulo: str
    resumen: str
    impacto_m3_mes: float | None = None
    recomendacion: str | None = None
    sector_id: int
    created_at: datetime
    estado: Literal["abierta", "atendida", "escalada"]
    explicacion: dict | None = None

class AlertsResponse(BaseModel):
    items: List[AlertRead]

class AckRequest(BaseModel):
    pin: str
    nota: str | None = None

class AckResponse(BaseModel):
    status: Literal["acknowledged"]
    by_user: str
    ts: datetime