# app/schemas.py
from datetime import datetime
from pydantic import BaseModel
from typing import List, Literal, Dict, Optional

class KPIResponse(BaseModel):
    """
    Respuesta de KPIs del tablero (encabezado).
    - ts: última marca de tiempo considerada.
    - eficiencia: promedio de eficiencia global (simulada).
    - tiempo_decision_min: SLA/tiempo objetivo para decisiones (min).
    - uso_datos_pct: % de uso de datos disponible.
    - sectores_en_riesgo: conteo de sectores con al menos una alerta abierta.
    """
    ts: str
    eficiencia: float
    eficiencia_trend: List[float]
    sectores_en_riesgo: int
    alertas_atendidas_24h: int
    tiempo_decision_min: int


class SectorCard(BaseModel):
    """
    Tarjeta de sector para el grid.
    - estado: 'normal' | 'alerta' | 'critico' según umbrales de eficiencia.
    - tendencia: serie corta (sparkline) de eficiencias recientes (orden cronológico).
    """
    id: int
    nombre: str
    estado: Literal["normal", "alerta", "critico"]
    eficiencia: float
    presion_psi: float
    alertas_abiertas: int
    tendencia: List[float]


class SectorsResponse(BaseModel):
    """Contenedor de lista de sectores para la ruta /sim/sectors."""
    items: List[SectorCard]


class AlertRead(BaseModel):
    """
    Alerta lista para UI (“inbox de problemas”).
    - titulo: resumen legible (ej. 'Posible fuga en Sector 233').
    - resumen: mensaje corto (regla que disparó).
    - impacto_m3_mes: estimación de impacto mensual (si aplica).
    - recomendacion: siguiente paso sugerido.
    - explicacion: diccionario con detalle; suele contener:
        {'raw': "{'base': 'historial_propio', 'feature': 'no_facturable_pct', 'value': 0.2, 'threshold': 0.1}"}
    """
    id: int
    nivel: Literal["alta", "media", "baja"]
    titulo: str
    resumen: str
    impacto_m3_mes: Optional[float] = None
    recomendacion: Optional[str] = None
    sector_id: int
    created_at: datetime
    estado: Literal["abierta", "atendida", "escalada"]
    explicacion: Optional[Dict] = None


class AlertsResponse(BaseModel):
    """Contenedor de lista de alertas para la ruta /sim/alerts."""
    items: List[AlertRead]


class AckRequest(BaseModel):
    """
    Petición para marcar una alerta como 'atendida' (ACK = acuse de recibo).
    - pin: PIN de autorización (demo).
    - nota: comentario opcional.
    """
    pin: str
    nota: Optional[str] = None


class AckResponse(BaseModel):
    """
    Respuesta tras atender una alerta.
    - status: siempre 'acknowledged' en esta demo.
    - by_user: usuario que atendió.
    - ts: tiempo del cambio de estado.
    """
    status: Literal["acknowledged"]
    by_user: str
    ts: datetime