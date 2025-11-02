# app/services/sim.py
import asyncio, math, random
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any
from sqlmodel import select
from ..db import ENGINE
from sqlmodel import Session
from ..models import Sector, Reading, Alert, ActionLog

# ----- Estado interno de simulación -----
_TASK: Optional[asyncio.Task] = None
_SUBSCRIBERS: "set[asyncio.Queue]" = set()

class EWMA:
    def __init__(self, alpha: float, init: float | None = None):
        self.alpha = alpha
        self.mean = init

    def update(self, x: float) -> float:
        if self.mean is None:
            self.mean = x
        else:
            self.mean = self.alpha * x + (1 - self.alpha) * self.mean
        return self.mean

class AR1:
    def __init__(self, phi: float, sigma: float, init: float):
        self.phi = phi
        self.sigma = sigma
        self.last = init

    def next(self, mu: float) -> float:
        # caminata mean-reverting
        eps = random.gauss(0, self.sigma)
        self.last = mu + self.phi * (self.last - mu) + eps
        return self.last

class SimState:
    def __init__(self, sector_ids: List[int]):
        self.eff_ewma: Dict[int, EWMA] = {sid: EWMA(0.3) for sid in sector_ids}
        self.pr_ewma: Dict[int, EWMA] = {sid: EWMA(0.3) for sid in sector_ids}
        self.eff_low_count: Dict[int, int] = defaultdict(int)
        self.trend_window: Dict[int, deque] = {sid: deque(maxlen=4) for sid in sector_ids}

# ----- Utilidades de negocio -----
def heat_multiplier(dt: datetime) -> float:
    # estacionalidad simple por hora; en calor “sube” el consumo
    h = dt.hour
    base = 1.0 + 0.15 * math.sin(2 * math.pi * (h / 24.0))
    return max(0.7, base)

def ensure_seed_sectors() -> List[int]:
    with Session(ENGINE) as s:
        existing = s.exec(select(Sector)).all()
        if not existing:
            nombres = [
                (233, "Sector 233"), (234, "Sector 234"), (145, "Sector 145"),
                (89, "Sector 089"),  (156, "Sector 156"), (201, "Sector 201"),
                (312, "Sector 312"), (78, "Sector 078"),
            ]
            for sid, nombre in nombres:
                s.add(Sector(id=sid, nombre=nombre, zona=None, activo=True))
            s.commit()
            return [sid for sid, _ in nombres]
        return [sec.id for sec in existing if sec.activo]

def simulate_reading(sector_id: int, when: datetime, ar_inj: AR1, ar_con: AR1, ar_pr: AR1):
    inj_mu = 120.0 * heat_multiplier(when)
    con_mu = 110.0 * heat_multiplier(when)
    pr_mu  = 40.0
    inyeccion = max(0.0, ar_inj.next(inj_mu))
    consumo   = max(0.001, ar_con.next(con_mu))
    presion   = max(5.0,  ar_pr.next(pr_mu))
    eficiencia = inyeccion / consumo
    return dict(sector_id=sector_id, ts=when, inyeccion_m3=inyeccion, consumo_m3=consumo, presion_psi=presion, eficiencia=eficiencia)

def evaluate_rules(r: Reading, eff_ewma: EWMA, pr_ewma: EWMA, eff_low_count: Dict[int, int]):
    alerts: List[Alert] = []
    eff_mean = eff_ewma.update(r.eficiencia)
    pr_mean  = pr_ewma.update(r.presion_psi)

    min_eff = 0.80
    if r.eficiencia < min_eff:
        eff_low_count[r.sector_id] += 1
    else:
        eff_low_count[r.sector_id] = 0

    if eff_low_count[r.sector_id] >= 2:
        msg = "Eficiencia < 80% sostenida (>= 2 ventanas)."
        exp = {"base":"historial_propio","feature":"eficiencia","value":r.eficiencia,"threshold":min_eff}
        alerts.append(Alert(sector_id=r.sector_id, nivel="alta", tipo="baja_eficiencia", mensaje=msg, explicacion=str(exp)))

    if pr_mean and abs(r.presion_psi - pr_mean)/pr_mean > 0.20:
        msg = "Presión ±20% vs su histórico (EWMA). Posible sobre/infra-presión."
        exp = {"base":"historial_propio","feature":"presion","value":r.presion_psi,"mean":pr_mean}
        alerts.append(Alert(sector_id=r.sector_id, nivel="media", tipo="sobrepresion", mensaje=msg, explicacion=str(exp)))

    no_fact = max(0.0, r.inyeccion_m3 - r.consumo_m3)
    if r.consumo_m3 > 0 and no_fact / r.consumo_m3 > 0.10:
        msg = "Consumo no facturable > 10% respecto a consumo."
        exp = {"base":"historial_propio","feature":"no_facturable_pct","value":no_fact/r.consumo_m3,"threshold":0.10}
        alerts.append(Alert(sector_id=r.sector_id, nivel="alta", tipo="no_facturable", mensaje=msg, explicacion=str(exp)))

    return alerts

# ----- API helpers (KPIs, sectores, alertas) -----
def compute_kpis() -> dict:
    with Session(ENGINE) as s:
        last = s.exec(select(Reading).order_by(Reading.ts.desc()).limit(500)).all()
        if not last:
            now = datetime.now(timezone.utc)
            return dict(ts=now, eficiencia=1.0, tiempo_decision_min=12, uso_datos_pct=0.76, sectores_en_riesgo=0)

        prom_eff = sum(x.eficiencia for x in last)/len(last)
        # aproximación: sectores en riesgo = alertas abiertas únicas por sector
        abiertas = s.exec(select(Alert).where(Alert.estado=="abierta")).all()
        sectores_riesgo = len({a.sector_id for a in abiertas})
        now = max(x.ts for x in last)
        return dict(ts=now, eficiencia=prom_eff, tiempo_decision_min=12, uso_datos_pct=0.76, sectores_en_riesgo=sectores_riesgo)

def sectors_grid() -> List[dict]:
    with Session(ENGINE) as s:
        sectores = s.exec(select(Sector).where(Sector.activo==True)).all()
        out = []
        for sec in sectores:
            last = s.exec(
                select(Reading).where(Reading.sector_id==sec.id).order_by(Reading.ts.desc()).limit(4)
            ).all()
            if not last:
                continue
            ult = last[0]
            eff = ult.eficiencia
            pr  = ult.presion_psi
            estado = "normal"
            if eff < 0.8: estado = "alerta"
            if eff < 0.7: estado = "critico"
            alertas_abiertas = s.exec(
                select(Alert).where(Alert.sector_id==sec.id, Alert.estado=="abierta")
            ).count()
            tendencia = [x.eficiencia for x in reversed(last)]
            out.append(dict(
                id=sec.id, nombre=sec.nombre, estado=estado,
                eficiencia=round(eff,3), presion_psi=round(pr,1),
                alertas_abiertas=alertas_abiertas, tendencia=tendencia
            ))
        return out

def list_alerts(status: str = "abierta") -> List[dict]:
    with Session(ENGINE) as s:
        qs = s.exec(select(Alert).where(Alert.estado==status).order_by(Alert.ts.desc()).limit(50)).all()
        items = []
        for a in qs:
            titulo = "Posible fuga" if a.tipo=="no_facturable" else ("Baja eficiencia" if a.tipo=="baja_eficiencia" else "Anomalía de presión")
            resumen = a.mensaje
            items.append(dict(
                id=a.id, nivel=a.nivel, titulo=f"{titulo} en Sector {a.sector_id}",
                resumen=resumen, impacto_m3_mes=4800.0 if a.tipo in ("no_facturable","baja_eficiencia") else None,
                recomendacion="Inspección en válvula 17. Prioridad Alta. Hoy." if a.nivel=="alta" else "Monitoreo y verificación en sitio.",
                sector_id=a.sector_id, created_at=a.ts, estado=a.estado,
                explicacion={"raw": a.explicacion} if a.explicacion else None
            ))
        return items

def acknowledge_alert(alert_id: int, user_email: str, nota: str | None):
    now = datetime.utcnow()
    with Session(ENGINE) as s:
        a = s.get(Alert, alert_id)
        if not a or a.estado != "abierta":
            return None
        a.estado = "atendida"
        a.atendida_por = user_email
        a.atendida_en = now
        s.add(ActionLog(alert_id=alert_id, actor=user_email, accion="ack", nota=nota))
        s.add(a)
        s.commit()
        return dict(status="acknowledged", by_user=user_email, ts=now)

# ----- Stream SSE -----
async def subscribe():
    q: asyncio.Queue = asyncio.Queue()
    _SUBSCRIBERS.add(q)
    try:
        while True:
            data = await q.get()
            yield data
    finally:
        _SUBSCRIBERS.discard(q)

def _broadcast(payload: dict):
    for q in list(_SUBSCRIBERS):
        if not q.full():
            q.put_nowait(payload)

# ----- Loop de simulación -----
async def _loop():
    sector_ids = ensure_seed_sectors()
    state = SimState(sector_ids)
    # inicializamos AR(1) por sector
    rng = random.Random(42)
    ar_inj = {sid: AR1(0.7, 5.0, 120.0) for sid in sector_ids}
    ar_con = {sid: AR1(0.7, 5.0, 110.0) for sid in sector_ids}
    ar_pr  = {sid: AR1(0.6, 1.5, 40.0)  for sid in sector_ids}

    # bootstrap inicial de lecturas para que el dashboard no esté vacío
    now = datetime.utcnow()
    with Session(ENGINE) as s:
        for sid in sector_ids:
            rdict = simulate_reading(sid, now, ar_inj[sid], ar_con[sid], ar_pr[sid])
            r = Reading(**rdict)
            s.add(r)
        s.commit()

    # cada 4 minutos (para demo puedes bajar a 10s)
    interval = int(240)  # 240s = 4 min
    demo_fast = True
    if demo_fast:
        interval = 10

    while True:
        tick = datetime.utcnow()
        with Session(ENGINE) as s:
            for sid in sector_ids:
                rdict = simulate_reading(sid, tick, ar_inj[sid], ar_con[sid], ar_pr[sid])
                r = Reading(**rdict)
                s.add(r)
                s.commit()

                alerts = evaluate_rules(
                    r,
                    state.eff_ewma[sid],
                    state.pr_ewma[sid],
                    state.eff_low_count
                )
                for a in alerts:
                    s.add(a)
                    s.commit()
                    _broadcast({"type": "alert", "payload": {"id": a.id, "sector_id": a.sector_id, "nivel": a.nivel, "tipo": a.tipo, "ts": a.ts.isoformat()}})

                # actualiza tendencia (para sparkline)
                state.trend_window[sid].append(r.eficiencia)
        _broadcast({"type":"tick","payload":{"ts":tick.isoformat()}})
        await asyncio.sleep(interval)

async def start_background_simulation():
    global _TASK
    if _TASK is None or _TASK.done():
        _TASK = asyncio.create_task(_loop())

async def stop_background_simulation():
    global _TASK
    if _TASK and not _TASK.done():
        _TASK.cancel()
        try:
            await _TASK
        except asyncio.CancelledError:
            pass