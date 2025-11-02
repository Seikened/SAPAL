# app/models.py
from datetime import datetime
from sqlmodel import SQLModel, Field

class Sector(SQLModel, table=True):
    """
    Tabla de sectores hidráulicos.
    - id: identificador del sector (clave primaria).
    - nombre: etiqueta legible.
    - zona: zona geográfica opcional.
    - activo: indica si el sector está operativo/visible.
    """
    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    zona: str | None = None
    activo: bool = True


class Reading(SQLModel, table=True):
    """
    Tabla de lecturas (telemetría/simulación) por sector y tiempo.
    - sector_id: FK a Sector.
    - ts: timestamp de la lectura (UTC).
    - inyeccion_m3: volumen inyectado al sector (m³).
    - consumo_m3: volumen consumido/medido (m³).
    - presion_psi: presión estimada (PSI).
    - eficiencia: inyección/consumo (adimensional). >1 puede indicar pérdidas o modelado.
    """
    id: int | None = Field(default=None, primary_key=True)
    sector_id: int = Field(index=True)
    ts: datetime = Field(default_factory=datetime.utcnow, index=True)
    inyeccion_m3: float
    consumo_m3: float
    presion_psi: float
    eficiencia: float


class Alert(SQLModel, table=True):
    """
    Tabla de alertas generadas por reglas de negocio.
    - nivel: 'alta' | 'media' | 'baja'.
    - tipo: 'baja_eficiencia' | 'sobrepresion' | 'no_facturable'.
    - mensaje: texto corto para UI.
    - explicacion: detalle (JSON serializado como str) con base/feature/valores/umbrales.
    - estado: 'abierta' | 'atendida' | 'escalada'.
    - atendida_por / atendida_en: tracking cuando se marca como atendida (ACK).
    - escalada_a / escalada_en: tracking cuando se escala.
    """
    id: int | None = Field(default=None, primary_key=True)
    sector_id: int = Field(index=True)
    ts: datetime = Field(default_factory=datetime.utcnow, index=True)
    nivel: str
    tipo: str
    mensaje: str
    explicacion: str | None = None
    estado: str = "abierta"
    atendida_por: str | None = None
    atendida_en: datetime | None = None
    escalada_a: str | None = None
    escalada_en: datetime | None = None


class ActionLog(SQLModel, table=True):
    """
    Bitácora de acciones sobre alertas (auditoría).
    - alert_id: FK a Alert.
    - actor: correo/usuario que ejecuta la acción.
    - accion: 'ack' (atender) | 'escalar'.
    - nota: observaciones libres.
    - ts: timestamp de la acción.
    """
    id: int | None = Field(default=None, primary_key=True)
    alert_id: int = Field(index=True)
    actor: str
    accion: str  # "ack" | "escalar"
    nota: str | None = None
    ts: datetime = Field(default_factory=datetime.utcnow)