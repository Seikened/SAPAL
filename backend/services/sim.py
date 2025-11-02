# app/services/sim.py
import asyncio
import json
import math
import random
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..db import SessionLocal
from ..models import ActionLog, Alert, Reading, Sector


# ─────────────────────────────────────────────────────────────
# Utilidad de sesión
# ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def contexto_sesion():
    sesion: AsyncSession = SessionLocal()
    try:
        yield sesion
    finally:
        await sesion.close()

# ─────────────────────────────────────────────────────────────
# Estado interno
# ─────────────────────────────────────────────────────────────
_TAREA_SIMULACION: Optional[asyncio.Task] = None
_SUSCRIPTORES: "set[asyncio.Queue]" = set()

class MediaMovilExponencial:
    def __init__(self, alpha: float, valor_inicial: Optional[float] = None):
        self.alpha = alpha
        self.media = valor_inicial

    def actualizar(self, valor: float) -> float:
        if self.media is None:
            self.media = valor
        else:
            self.media = self.alpha * valor + (1 - self.alpha) * self.media
        return self.media

class ProcesoAR1:
    def __init__(self, coeficiente: float, desviacion: float, inicial: float):
        self.coeficiente = coeficiente
        self.desviacion = desviacion
        self.ultimo = inicial

    def siguiente(self, media_objetivo: float) -> float:
        ruido = random.gauss(0, self.desviacion)
        self.ultimo = media_objetivo + self.coeficiente * (self.ultimo - media_objetivo) + ruido
        return self.ultimo

class EstadoSimulacion:
    def __init__(self, ids_sectores: List[int]):
        self.medias_moviles_eficiencia: Dict[int, MediaMovilExponencial] = {sid: MediaMovilExponencial(0.3) for sid in ids_sectores}
        self.medias_moviles_presion: Dict[int, MediaMovilExponencial] = {sid: MediaMovilExponencial(0.3) for sid in ids_sectores}
        self.conteo_baja_eficiencia: Dict[int, int] = defaultdict(int)
        self.ventana_tendencia: Dict[int, deque] = {sid: deque(maxlen=4) for sid in ids_sectores}

# ─────────────────────────────────────────────────────────────
# Utilidades de negocio
# ─────────────────────────────────────────────────────────────
def factor_estacional_por_hora(instante: datetime) -> float:
    hora = instante.hour
    base = 1.0 + 0.15 * math.sin(2 * math.pi * (hora / 24.0))
    return max(0.7, base)

async def asegurar_sectores_semilla() -> List[int]:
    async with contexto_sesion() as sesion:
        res = await sesion.execute(select(Sector))
        existentes = res.scalars().all()
        if not existentes:
            sectores = [(233, "Sector 233"), (234, "Sector 234"), (145, "Sector 145"),
                        (89, "Sector 089"), (156, "Sector 156"), (201, "Sector 201"),
                        (312, "Sector 312"), (78, "Sector 078")]
            async with sesion.begin():
                for sid, nombre in sectores:
                    sesion.add(Sector(id=sid, nombre=nombre, zona=None, activo=True))
            return [sid for sid, _ in sectores]
        return [sec.id for sec in existentes if sec.activo]

# Perfiles e incidentes (se inicializan en _bucle_simulacion)
_PERFILES: Dict[int, dict] = {}
_INCIDENTES: Dict[int, dict] = {}

def _crear_perfiles(ids: List[int]) -> Dict[int, dict]:
    return {
        sid: {
            "loss_base": random.uniform(0.05, 0.12),          # 5–12% pérdida base
            "pressure_nom": random.uniform(38.0, 42.0),       # PSI nominal
            "season_bias": random.uniform(0.9, 1.1),          # sensibilidad a calor
        } for sid in ids
    }

def _levanta_incidente(si: int, instante: datetime, intervalo: int):
    tipo = random.choice(["fuga", "sobrepresion", "baja_disponibilidad"])
    dur_ticks = random.randint(3, 6)  # 30–60s si intervalo=10
    _INCIDENTES[si] = {
        "tipo": tipo,
        "intensidad": random.uniform(0.5, 1.0),
        "hasta": instante + timedelta(seconds=dur_ticks * intervalo),
    }

def simular_lectura(
    id_sector: int,
    instante: datetime,
    proceso_inyeccion: ProcesoAR1,
    proceso_consumo: ProcesoAR1,
    proceso_presion: ProcesoAR1,
) -> dict:
    # Demanda objetivo (consumo) con estacionalidad y sesgo por sector
    est = factor_estacional_por_hora(instante)
    perfil = _PERFILES[id_sector]
    demanda = 110.0 * est * perfil["season_bias"]

    # Pérdida base por sector
    loss_base = demanda * perfil["loss_base"]

    # Incidente activo modifica demanda/pérdida/presión
    incidente = _INCIDENTES.get(id_sector)
    demanda_mod = demanda
    loss_extra = 0.0
    pnom = perfil["pressure_nom"]
    presion_nominal = pnom

    if incidente and incidente["hasta"] > instante:
        inten = incidente["intensidad"]
        if incidente["tipo"] == "fuga":
            loss_extra = demanda * random.uniform(0.08, 0.20) * inten
        elif incidente["tipo"] == "baja_disponibilidad":
            demanda_mod = demanda * (1.0 - random.uniform(0.10, 0.25) * inten)
            presion_nominal = pnom * (0.80 + random.gauss(0, 0.03))
        elif incidente["tipo"] == "sobrepresion":
            presion_nominal = pnom * (1.25 + random.gauss(0, 0.03))

    # Consumo con pequeño ruido
    consumo_obj = max(0.001, demanda_mod * (1.0 + random.gauss(0, 0.02)))
    # Pérdida total
    perdida = max(0.0, loss_base + loss_extra)
    # Inyección = consumo + pérdida
    inyeccion_obj = max(consumo_obj + perdida, 0.001)

    # Pasar por AR(1) para suavidad temporal
    inyeccion = max(0.0, proceso_inyeccion.siguiente(inyeccion_obj))
    consumo = max(0.001, proceso_consumo.siguiente(consumo_obj))
    presion = max(5.0, proceso_presion.siguiente(presion_nominal))

    eficiencia = inyeccion / consumo  # >1 cuando hay pérdidas
    return dict(
        sector_id=id_sector,
        ts=instante,
        inyeccion_m3=inyeccion,
        consumo_m3=consumo,
        presion_psi=presion,
        eficiencia=eficiencia,
    )

def evaluar_reglas_alertas(
    lectura: Reading,
    media_mov_eficiencia: MediaMovilExponencial,
    media_mov_presion: MediaMovilExponencial,
    conteo_baja_eficiencia: Dict[int, int],
) -> List[Alert]:
    alertas: List[Alert] = []

    media_eficiencia = media_mov_eficiencia.actualizar(lectura.eficiencia)
    media_presion = media_mov_presion.actualizar(lectura.presion_psi)

    # Eficiencia operativa (consumo/inyección) y pérdida relativa
    eficiencia_operativa = lectura.consumo_m3 / max(lectura.inyeccion_m3, 0.001)
    loss_pct = max(0.0, lectura.inyeccion_m3 - lectura.consumo_m3) / lectura.consumo_m3

    # 1) Baja eficiencia operativa sostenida
    if eficiencia_operativa < 0.85:
        conteo_baja_eficiencia[lectura.sector_id] += 1
    else:
        conteo_baja_eficiencia[lectura.sector_id] = 0

    if conteo_baja_eficiencia[lectura.sector_id] >= 2:
        detalle = {
            "base": "historial_propio",
            "caracteristica": "eficiencia_operativa",
            "valor": eficiencia_operativa,
            "umbral": 0.85,
        }
        alertas.append(Alert(
            sector_id=lectura.sector_id,
            nivel="alta",
            tipo="baja_eficiencia",
            mensaje="Eficiencia operativa < 85% sostenida (≥2 ventanas).",
            explicacion=json.dumps(detalle),
        ))

    # 2) Presión desviada ±20% vs EWMA
    if media_presion and abs(lectura.presion_psi - media_presion) / media_presion > 0.20:
        detalle = {
            "base": "historial_propio",
            "caracteristica": "presion",
            "valor": lectura.presion_psi,
            "media": media_presion,
        }
        alertas.append(Alert(
            sector_id=lectura.sector_id,
            nivel="media",
            tipo="sobrepresion",
            mensaje="Presión ±20% vs su histórico (EWMA).",
            explicacion=json.dumps(detalle),
        ))

    # 3) No facturable alto > 15%
    if loss_pct > 0.15:
        detalle = {
            "base": "historial_propio",
            "caracteristica": "no_facturable_pct",
            "valor": loss_pct,
            "umbral": 0.15,
        }
        alertas.append(Alert(
            sector_id=lectura.sector_id,
            nivel="alta",
            tipo="no_facturable",
            mensaje="Consumo no facturable > 15% respecto a consumo.",
            explicacion=json.dumps(detalle),
        ))

    return alertas

# ─────────────────────────────────────────────────────────────
# Funciones llamadas por las rutas
# ─────────────────────────────────────────────────────────────


async def calcular_kpis() -> dict:
    """
    Calcula KPIs:
      - eficiencia: promedio global del último tick
      - eficiencia_trend: promedio global por tick (últimos N)
      - sectores_en_riesgo: sectores con alertas abiertas
      - alertas_atendidas_24h: conteo en las últimas 24h
    """
    async with contexto_sesion() as sesion:
        # Trae lecturas recientes (500 suele bastar para 16 ticks x ~8 sectores)
        res = await sesion.execute(
            select(Reading).order_by(Reading.ts.desc()).limit(500)
        )
        lecturas = res.scalars().all()

        if not lecturas:
            ahora = datetime.now(timezone.utc)
            return dict(
                ts=ahora.isoformat(),
                eficiencia=1.0,
                eficiencia_trend=[1.0],
                sectores_en_riesgo=0,
                alertas_atendidas_24h=0,
                tiempo_decision_min=12,
            )

        # Agrupa por ts exacto (cada tick inserta una lectura por sector con el mismo ts)
        por_ts: dict[datetime, list[float]] = defaultdict(list)
        for l in lecturas:
            por_ts[l.ts].append(float(l.eficiencia))

        # Orden cronológico (asc) y promedios por tick
        ts_ordenados = sorted(por_ts.keys())
        proms = [sum(vals)/len(vals) for t, vals in sorted(por_ts.items())]

        # Últimos N puntos para la sparkline
        N = 16
        eficiencia_trend = proms[-N:] if len(proms) > N else proms
        eficiencia = eficiencia_trend[-1]
        ts_reciente = ts_ordenados[-1].isoformat()

        # Sectores en riesgo = sectores con alertas abiertas
        q_abiertas = await sesion.execute(
            select(Alert).where(Alert.estado == "abierta")
        )
        alertas_abiertas = q_abiertas.scalars().all()
        sectores_en_riesgo = len({a.sector_id for a in alertas_abiertas})

        # Atendidas últimas 24h
        hace_24 = datetime.now(timezone.utc) - timedelta(hours=24)
        atendidas_24h = await sesion.execute(
            select(func.count(Alert.id)).where(
                Alert.estado == "atendida",
                Alert.atendida_en >= hace_24
            )
        )
        alertas_atendidas_24h = int(atendidas_24h.scalar_one())

        return dict(
            ts=ts_reciente,
            eficiencia=eficiencia,
            eficiencia_trend=eficiencia_trend,
            sectores_en_riesgo=sectores_en_riesgo,
            alertas_atendidas_24h=alertas_atendidas_24h,
            tiempo_decision_min=12,
        )

async def construir_cuadricula_sectores() -> List[dict]:
    async with contexto_sesion() as sesion:
        resp_sec = await sesion.execute(select(Sector).where(Sector.activo.is_(True)))
        sectores = resp_sec.scalars().all()
        salida: List[dict] = []

        for sector in sectores:
            resp_lect = await sesion.execute(
                select(Reading)
                .where(Reading.sector_id == sector.id)
                .order_by(Reading.ts.desc())
                .limit(4)
            )
            lecturas = resp_lect.scalars().all()
            if not lecturas:
                continue

            lectura_reciente = lecturas[0]
            eficiencia_operativa = float(lectura_reciente.consumo_m3 / max(lectura_reciente.inyeccion_m3, 0.001))
            presion_actual = float(lectura_reciente.presion_psi)
            loss_pct = float(max(0.0, lectura_reciente.inyeccion_m3 - lectura_reciente.consumo_m3) / lectura_reciente.consumo_m3)

            # estado por reglas simples
            estado = "normal"
            if loss_pct > 0.12 or eficiencia_operativa < 0.9:
                estado = "alerta"
            if loss_pct > 0.2 or eficiencia_operativa < 0.85:
                estado = "critico"

            # alertas abiertas
            res_cnt = await sesion.execute(
                select(func.count(Alert.id)).where(
                    Alert.sector_id == sector.id,
                    Alert.estado == "abierta",
                )
            )
            cantidad_alertas_abiertas = res_cnt.scalar_one()

            tendencia = [float(r.consumo_m3 / max(r.inyeccion_m3, 0.001)) for r in reversed(lecturas)]

            salida.append({
                "id": sector.id,
                "nombre": sector.nombre,
                "estado": estado,  # "normal" | "alerta" | "critico"
                "eficiencia": round(eficiencia_operativa, 3),   # 0..1 en UI tú lo formateas a %
                "presion_psi": round(presion_actual, 1),
                "alertas_abiertas": int(cantidad_alertas_abiertas),
                "tendencia": tendencia,
            })

        return salida

async def listar_alertas(estado: str = "abierta") -> List[dict]:
    estado = (estado or "").lower()
    estados_validos = {"abierta", "atendida", "escalada"}
    if estado not in estados_validos:
        estado = "abierta"

    titulo_por_tipo = {
        "no_facturable": "Posible fuga",
        "baja_eficiencia": "Baja eficiencia",
        "sobrepresion": "Anomalía de presión",
    }

    async with contexto_sesion() as sesion:
        res = await sesion.execute(
            select(Alert)
            .where(Alert.estado == estado)
            .order_by(Alert.ts.desc())
            .limit(50)
        )
        alertas = res.scalars().all()

        elementos: list[dict] = []
        for alerta in alertas:
            titulo = titulo_por_tipo.get(alerta.tipo, "Alerta")
            recomendacion = (
                "Inspección en válvula 17. Prioridad alta. Hoy."
                if alerta.nivel == "alta"
                else "Monitoreo y verificación en sitio."
            )
            explicacion_dict = None
            if alerta.explicacion:
                try:
                    explicacion_dict = json.loads(alerta.explicacion)
                except Exception:
                    explicacion_dict = {"raw": alerta.explicacion}

            elementos.append({
                "id": alerta.id,
                "nivel": alerta.nivel,
                "tipo": alerta.tipo,
                "titulo": f"{titulo} en Sector {alerta.sector_id}",
                "resumen": alerta.mensaje,
                "impacto_m3_mes": 4800.0 if alerta.tipo in ("no_facturable", "baja_eficiencia") else None,
                "recomendacion": recomendacion,
                "sector_id": alerta.sector_id,
                "created_at": alerta.ts,
                "estado": alerta.estado,
                "explicacion": explicacion_dict,
            })

        return elementos

async def atender_alerta(id_alerta: int, correo_usuario: str, nota: Optional[str]):
    ahora = datetime.now(timezone.utc)
    async with contexto_sesion() as sesion:
        async with sesion.begin():
            res = await sesion.execute(select(Alert).where(Alert.id == id_alerta))
            alerta = res.scalar_one_or_none()
            if not alerta or alerta.estado != "abierta":
                return None
            alerta.estado = "atendida"
            alerta.atendida_por = correo_usuario
            alerta.atendida_en = ahora
            sesion.add(ActionLog(alert_id=id_alerta, actor=correo_usuario, accion="ack", nota=nota))
        return {"status": "acknowledged", "by_user": correo_usuario, "ts": ahora}

# ─────────────────────────────────────────────────────────────
# SSE (opcional, sigue funcionando para toasts)
# ─────────────────────────────────────────────────────────────
async def suscribirse_eventos():
    cola: asyncio.Queue = asyncio.Queue()
    _SUSCRIPTORES.add(cola)
    try:
        while True:
            dato = await cola.get()
            yield dato
    finally:
        _SUSCRIPTORES.discard(cola)

def _difundir(payload: dict):
    for cola in list(_SUSCRIPTORES):
        if not cola.full():
            cola.put_nowait(payload)

# ─────────────────────────────────────────────────────────────
# Bucle de simulación
# ─────────────────────────────────────────────────────────────
async def _bucle_simulacion():
    ids_sectores = await asegurar_sectores_semilla()
    estado = EstadoSimulacion(ids_sectores)

    # Perfiles por sector e incidentes
    global _PERFILES, _INCIDENTES
    _PERFILES = _crear_perfiles(ids_sectores)
    _INCIDENTES = {}

    procesos_inyeccion = {sid: ProcesoAR1(0.7, 5.0, 120.0) for sid in ids_sectores}
    procesos_consumo   = {sid: ProcesoAR1(0.7, 5.0, 110.0) for sid in ids_sectores}
    procesos_presion   = {sid: ProcesoAR1(0.6, 1.5, _PERFILES[sid]["pressure_nom"]) for sid in ids_sectores}

    # Bootstrap inicial para que el dashboard no arranque vacío
    ahora = datetime.now(timezone.utc)
    async with contexto_sesion() as sesion:
        async with sesion.begin():
            for sid in ids_sectores:
                datos = simular_lectura(sid, ahora, procesos_inyeccion[sid], procesos_consumo[sid], procesos_presion[sid])
                sesion.add(Reading(**datos))
        await sesion.commit()

    intervalo_segundos = 10  # demo

    while True:
        instante = datetime.now(timezone.utc)

        # gestionar incidentes por sector
        for sid in ids_sectores:
            # limpiar expirados
            inc = _INCIDENTES.get(sid)
            if inc and inc["hasta"] <= instante:
                _INCIDENTES.pop(sid, None)
            # chance de iniciar uno si no hay activo
            if sid not in _INCIDENTES and random.random() < 0.01:
                _levanta_incidente(sid, instante, intervalo_segundos)

        async with contexto_sesion() as sesion:
            async with sesion.begin():
                for sid in ids_sectores:
                    datos = simular_lectura(sid, instante, procesos_inyeccion[sid], procesos_consumo[sid], procesos_presion[sid])
                    lectura = Reading(**datos)
                    sesion.add(lectura)

                    nuevas = evaluar_reglas_alertas(
                        lectura,
                        estado.medias_moviles_eficiencia[sid],
                        estado.medias_moviles_presion[sid],
                        estado.conteo_baja_eficiencia
                    )
                    for alerta in nuevas:
                        sesion.add(alerta)
                        _difundir({
                            "type": "alert",
                            "payload": {
                                "id": alerta.id, "sector_id": alerta.sector_id,
                                "nivel": alerta.nivel, "tipo": alerta.tipo,
                                "ts": alerta.ts.isoformat(),
                            }
                        })

                    estado.ventana_tendencia[sid].append(lectura.consumo_m3 / max(lectura.inyeccion_m3, 0.001))

        _difundir({"type": "tick", "payload": {"ts": instante.isoformat()}})
        await asyncio.sleep(intervalo_segundos)

async def iniciar_simulacion_segundo_plano():
    global _TAREA_SIMULACION
    if _TAREA_SIMULACION is None or _TAREA_SIMULACION.done():
        _TAREA_SIMULACION = asyncio.create_task(_bucle_simulacion())

async def detener_simulacion_segundo_plano():
    global _TAREA_SIMULACION
    if _TAREA_SIMULACION and not _TAREA_SIMULACION.done():
        _TAREA_SIMULACION.cancel()
        try:
            await _TAREA_SIMULACION
        except asyncio.CancelledError:
            pass
