# app/services/sim.py
import asyncio
import math
import random
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from collections import defaultdict, deque
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlmodel import select, Session

from ..db import ENGINE
from ..models import Sector, Reading, Alert, ActionLog


# ─────────────────────────────────────────────────────────────
# Utilidad para evitar repetir "with Session(ENGINE) as s:"
# ─────────────────────────────────────────────────────────────
@contextmanager
def contexto_sesion():
    """
    Abre una sesión de base de datos y la cierra automáticamente.
    Evita repetir boilerplate en cada función.
    """
    sesion = Session(ENGINE)
    try:
        yield sesion
    finally:
        sesion.close()


# ─────────────────────────────────────────────────────────────
# Estado interno de simulación (no persistente)
# ─────────────────────────────────────────────────────────────
_TAREA_SIMULACION: Optional[asyncio.Task] = None
_SUSCRIPTORES: "set[asyncio.Queue]" = set()


class MediaMovilExponencial:
    """
    Media móvil exponencial para suavizar series (histórico corto).
    """
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
    """
    Proceso autoregresivo de orden 1 (AR(1)) con tendencia a la media.
    Genera series realistas para la simulación.
    """
    def __init__(self, coeficiente: float, desviacion: float, inicial: float):
        self.coeficiente = coeficiente
        self.desviacion = desviacion
        self.ultimo = inicial

    def siguiente(self, media_objetivo: float) -> float:
        ruido = random.gauss(0, self.desviacion)
        self.ultimo = media_objetivo + self.coeficiente * (self.ultimo - media_objetivo) + ruido
        return self.ultimo


class EstadoSimulacion:
    """
    Estructura auxiliar por sector:
    - medias_moviles_eficiencia / medias_moviles_presion: suavizado EWMA.
    - conteo_baja_eficiencia: ventanas consecutivas con eficiencia baja.
    - ventana_tendencia: últimas eficiencias para sparkline.
    """
    def __init__(self, ids_sectores: List[int]):
        self.medias_moviles_eficiencia: Dict[int, MediaMovilExponencial] = {
            sid: MediaMovilExponencial(0.3) for sid in ids_sectores
        }
        self.medias_moviles_presion: Dict[int, MediaMovilExponencial] = {
            sid: MediaMovilExponencial(0.3) for sid in ids_sectores
        }
        self.conteo_baja_eficiencia: Dict[int, int] = defaultdict(int)
        self.ventana_tendencia: Dict[int, deque] = {sid: deque(maxlen=4) for sid in ids_sectores}


# ─────────────────────────────────────────────────────────────
# Utilidades de negocio (nombres y variables en español)
# ─────────────────────────────────────────────────────────────
def factor_estacional_por_hora(instante: datetime) -> float:
    """
    Factor estacional sencillo por hora del día.
    Interpreta mayor consumo en horas “cálidas”.
    """
    hora = instante.hour
    base = 1.0 + 0.15 * math.sin(2 * math.pi * (hora / 24.0))
    return max(0.7, base)


def asegurar_sectores_semilla() -> List[int]:
    """
    Garantiza que existan sectores iniciales.
    Devuelve los ids de sectores activos.
    """
    with contexto_sesion() as sesion:
        existentes = sesion.exec(select(Sector)).all()
        if not existentes:
            sectores = [
                (233, "Sector 233"), (234, "Sector 234"), (145, "Sector 145"),
                (89, "Sector 089"),  (156, "Sector 156"), (201, "Sector 201"),
                (312, "Sector 312"), (78, "Sector 078"),
            ]
            for sid, nombre in sectores:
                sesion.add(Sector(id=sid, nombre=nombre, zona=None, activo=True))
            sesion.commit()
            return [sid for sid, _ in sectores]
        return [sec.id for sec in existentes if sec.activo]


def simular_lectura(
    id_sector: int,
    instante: datetime,
    proceso_inyeccion: ProcesoAR1,
    proceso_consumo: ProcesoAR1,
    proceso_presion: ProcesoAR1,
) -> dict:
    """
    Genera una lectura sintética coherente para un sector en un instante.
    """
    media_inyeccion = 120.0 * factor_estacional_por_hora(instante)
    media_consumo = 110.0 * factor_estacional_por_hora(instante)
    media_presion = 40.0

    inyeccion = max(0.0,  proceso_inyeccion.siguiente(media_inyeccion))
    consumo   = max(0.001, proceso_consumo.siguiente(media_consumo))
    presion   = max(5.0,  proceso_presion.siguiente(media_presion))
    eficiencia = inyeccion / consumo

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
    """
    Aplica reglas de negocio y devuelve las alertas a persistir:

    1) Eficiencia sostenida < 0.80 por al menos 2 ventanas.
    2) Desviación de presión ±20% contra su media móvil (EWMA).
    3) No facturable: (inyección - consumo) / consumo > 0.10.
    """
    alertas: List[Alert] = []

    media_eficiencia = media_mov_eficiencia.actualizar(lectura.eficiencia)
    media_presion = media_mov_presion.actualizar(lectura.presion_psi)

    umbral_eficiencia = 0.80
    if lectura.eficiencia < umbral_eficiencia:
        conteo_baja_eficiencia[lectura.sector_id] += 1
    else:
        conteo_baja_eficiencia[lectura.sector_id] = 0

    if conteo_baja_eficiencia[lectura.sector_id] >= 2:
        mensaje = "Eficiencia < 80% sostenida (≥ 2 ventanas)."
        detalle = {
            "base": "historial_propio",
            "caracteristica": "eficiencia",
            "valor": lectura.eficiencia,
            "umbral": umbral_eficiencia,
        }
        alertas.append(Alert(
            sector_id=lectura.sector_id,
            nivel="alta",
            tipo="baja_eficiencia",
            mensaje=mensaje,
            explicacion=json.dumps(detalle),
        ))

    if media_presion and abs(lectura.presion_psi - media_presion) / media_presion > 0.20:
        mensaje = "Presión ±20% vs su histórico (EWMA). Posible sobre/infra-presión."
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
            mensaje=mensaje,
            explicacion=json.dumps(detalle),
        ))

    volumen_no_facturable = max(0.0, lectura.inyeccion_m3 - lectura.consumo_m3)
    if lectura.consumo_m3 > 0 and volumen_no_facturable / lectura.consumo_m3 > 0.10:
        mensaje = "Consumo no facturable > 10% respecto a consumo."
        detalle = {
            "base": "historial_propio",
            "caracteristica": "no_facturable_pct",
            "valor": volumen_no_facturable / lectura.consumo_m3,
            "umbral": 0.10,
        }
        alertas.append(Alert(
            sector_id=lectura.sector_id,
            nivel="alta",
            tipo="no_facturable",
            mensaje=mensaje,
            explicacion=json.dumps(detalle),
        ))

    return alertas


# ─────────────────────────────────────────────────────────────
# Funciones usadas por las rutas (KPIs, sectores, alertas, ACK)
# ─────────────────────────────────────────────────────────────
def calcular_kpis() -> dict:
    """
    Calcula KPIs del encabezado del tablero.
    """
    with contexto_sesion() as sesion:
        lecturas = sesion.exec(
            select(Reading).order_by(Reading.ts.desc()).limit(500)
        ).all()

        if not lecturas:
            ahora = datetime.now(timezone.utc)
            return dict(
                ts=ahora,
                eficiencia=1.0,
                tiempo_decision_min=12,
                uso_datos_pct=0.76,
                sectores_en_riesgo=0,
            )

        eficiencia_promedio = sum(l.eficiencia for l in lecturas) / len(lecturas)
        alertas_abiertas = sesion.exec(
            select(Alert).where(Alert.estado == "abierta")
        ).all()
        sectores_en_riesgo = len({a.sector_id for a in alertas_abiertas})
        ts_reciente = max(l.ts for l in lecturas)

        return dict(
            ts=ts_reciente,
            eficiencia=eficiencia_promedio,
            tiempo_decision_min=12,
            uso_datos_pct=0.76,
            sectores_en_riesgo=sectores_en_riesgo,
        )


def construir_cuadricula_sectores() -> List[dict]:
    """
    Construye las tarjetas de sectores para el grid del dashboard.
    Incluye estado semaforizado y pequeña serie de tendencia.
    """
    with contexto_sesion() as sesion:
        sectores = sesion.exec(select(Sector).where(Sector.activo == True)).all()
        salida: List[dict] = []

        for sector in sectores:
            lecturas = sesion.exec(
                select(Reading)
                .where(Reading.sector_id == sector.id)
                .order_by(Reading.ts.desc())
                .limit(4)
            ).all()
            if not lecturas:
                continue

            lectura_reciente = lecturas[0]
            eficiencia_actual = float(lectura_reciente.eficiencia)
            presion_actual = float(lectura_reciente.presion_psi)

            estado = "normal"
            if eficiencia_actual < 0.8:
                estado = "alerta"
            if eficiencia_actual < 0.7:
                estado = "critico"

            cantidad_alertas_abiertas = sesion.exec(
                select(func.count(Alert.id)).where(
                    Alert.sector_id == sector.id,
                    Alert.estado == "abierta",
                )
            ).one()

            tendencia = [float(l.eficiencia) for l in reversed(lecturas)]

            salida.append({
                "id": sector.id,
                "nombre": sector.nombre,
                "estado": estado,
                "eficiencia": round(eficiencia_actual, 3),
                "presion_psi": round(presion_actual, 1),
                "alertas_abiertas": int(cantidad_alertas_abiertas),
                "tendencia": tendencia,
            })

        return salida


def listar_alertas(estado: str = "abierta") -> List[dict]:
    """
    Lista las alertas filtradas por estado, con títulos legibles y recomendación.
    """
    with contexto_sesion() as sesion:
        query = sesion.exec(
            select(Alert)
            .where(Alert.estado == estado)
            .order_by(Alert.ts.desc())
            .limit(50)
        ).all()

        elementos: List[dict] = []
        for alerta in query:
            if alerta.tipo == "no_facturable":
                titulo = "Posible fuga"
            elif alerta.tipo == "baja_eficiencia":
                titulo = "Baja eficiencia"
            else:
                titulo = "Anomalía de presión"

            recomendacion = (
                "Inspección en válvula 17. Prioridad alta. Hoy."
                if alerta.nivel == "alta"
                else "Monitoreo y verificación en sitio."
            )

            elementos.append({
                "id": alerta.id,
                "nivel": alerta.nivel,
                "titulo": f"{titulo} en Sector {alerta.sector_id}",
                "resumen": alerta.mensaje,
                "impacto_m3_mes": 4800.0 if alerta.tipo in ("no_facturable", "baja_eficiencia") else None,
                "recomendacion": recomendacion,
                "sector_id": alerta.sector_id,
                "created_at": alerta.ts,
                "estado": alerta.estado,
                "explicacion": {"raw": alerta.explicacion} if alerta.explicacion else None,
            })

        return elementos


def atender_alerta(id_alerta: int, correo_usuario: str, nota: Optional[str]):
    """
    Marca una alerta como 'atendida' (ACK) y registra la acción en bitácora.
    """
    ahora = datetime.utcnow()
    with contexto_sesion() as sesion:
        alerta = sesion.get(Alert, id_alerta)
        if not alerta or alerta.estado != "abierta":
            return None

        alerta.estado = "atendida"
        alerta.atendida_por = correo_usuario
        alerta.atendida_en = ahora

        sesion.add(ActionLog(
            alert_id=id_alerta,
            actor=correo_usuario,
            accion="ack",
            nota=nota,
        ))
        sesion.add(alerta)
        sesion.commit()

        return dict(status="acknowledged", by_user=correo_usuario, ts=ahora)


# ─────────────────────────────────────────────────────────────
# Flujo de eventos SSE (suscripción y difusión)
# ─────────────────────────────────────────────────────────────
async def suscribirse_eventos():
    """
    Generador asíncrono usado por el endpoint SSE.
    Entrega mensajes de tipo 'alert' y 'tick' a cada suscriptor.
    """
    cola: asyncio.Queue = asyncio.Queue()
    _SUSCRIPTORES.add(cola)
    try:
        while True:
            dato = await cola.get()
            yield dato
    finally:
        _SUSCRIPTORES.discard(cola)


def _difundir(payload: dict):
    """
    Envía un payload a todos los suscriptores conectados al SSE.
    """
    for cola in list(_SUSCRIPTORES):
        if not cola.full():
            cola.put_nowait(payload)


# ─────────────────────────────────────────────────────────────
# Bucle principal de simulación en segundo plano
# ─────────────────────────────────────────────────────────────
async def _bucle_simulacion():
    """
    - Crea sectores semilla si no existen.
    - Inicializa estado de simulación y procesos AR(1).
    - Inserta lecturas periódicas, evalúa reglas y emite eventos SSE.
    """
    ids_sectores = asegurar_sectores_semilla()
    estado = EstadoSimulacion(ids_sectores)

    procesos_inyeccion = {sid: ProcesoAR1(0.7, 5.0, 120.0) for sid in ids_sectores}
    procesos_consumo   = {sid: ProcesoAR1(0.7, 5.0, 110.0) for sid in ids_sectores}
    procesos_presion   = {sid: ProcesoAR1(0.6, 1.5, 40.0)  for sid in ids_sectores}

    # Bootstrap para que el dashboard no arranque vacío.
    ahora = datetime.utcnow()
    with contexto_sesion() as sesion:
        for sid in ids_sectores:
            datos_lectura = simular_lectura(
                sid, ahora, procesos_inyeccion[sid], procesos_consumo[sid], procesos_presion[sid]
            )
            sesion.add(Reading(**datos_lectura))
        sesion.commit()

    intervalo_segundos = 10  # demo rápida

    while True:
        instante = datetime.utcnow()
        with contexto_sesion() as sesion:
            for sid in ids_sectores:
                datos_lectura = simular_lectura(
                    sid, instante, procesos_inyeccion[sid], procesos_consumo[sid], procesos_presion[sid]
                )
                lectura = Reading(**datos_lectura)
                sesion.add(lectura)
                sesion.commit()

                nuevas_alertas = evaluar_reglas_alertas(
                    lectura,
                    estado.medias_moviles_eficiencia[sid],
                    estado.medias_moviles_presion[sid],
                    estado.conteo_baja_eficiencia
                )
                for alerta in nuevas_alertas:
                    sesion.add(alerta)
                    sesion.commit()
                    _difundir({
                        "type": "alert",
                        "payload": {
                            "id": alerta.id,
                            "sector_id": alerta.sector_id,
                            "nivel": alerta.nivel,
                            "tipo": alerta.tipo,
                            "ts": alerta.ts.isoformat(),
                        }
                    })

                estado.ventana_tendencia[sid].append(lectura.eficiencia)

        _difundir({"type": "tick", "payload": {"ts": instante.isoformat()}})
        await asyncio.sleep(intervalo_segundos)


async def iniciar_simulacion_segundo_plano():
    """
    Arranca la tarea asíncrona del bucle de simulación si no está activa.
    """
    global _TAREA_SIMULACION
    if _TAREA_SIMULACION is None or _TAREA_SIMULACION.done():
        _TAREA_SIMULACION = asyncio.create_task(_bucle_simulacion())


async def detener_simulacion_segundo_plano():
    """
    Detiene la tarea asíncrona del bucle de simulación si está activa.
    """
    global _TAREA_SIMULACION
    if _TAREA_SIMULACION and not _TAREA_SIMULACION.done():
        _TAREA_SIMULACION.cancel()
        try:
            await _TAREA_SIMULACION
        except asyncio.CancelledError:
            pass