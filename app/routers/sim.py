# app/routers/sim.py
import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..schemas import (
    KPIResponse,
    SectorsResponse,
    AlertsResponse,
    AckRequest,
    AckResponse,
)
from ..services import sim as servicios_sim

router = APIRouter()


@router.get("/kpis/current", response_model=KPIResponse)
async def obtener_kpis_actuales():
    """
    Devuelve los KPIs del encabezado del tablero.
    """
    datos = await servicios_sim.calcular_kpis()
    return {
        "ts": datos["ts"],
        "eficiencia": round(datos["eficiencia"], 3),
        "tiempo_decision_min": datos["tiempo_decision_min"],
        "uso_datos_pct": round(datos["uso_datos_pct"], 2),
        "sectores_en_riesgo": datos["sectores_en_riesgo"],
    }


@router.get("/sectors", response_model=SectorsResponse)
async def obtener_sectores():
    """
    Devuelve la cuadrícula de sectores para el dashboard.
    """
    elementos = await servicios_sim.construir_cuadricula_sectores()
    return {"items": elementos}


@router.get("/alerts", response_model=AlertsResponse)
async def obtener_alertas(estado: str = "abierta"):
    """
    Devuelve el listado de alertas filtrado por estado.
    """
    elementos = await servicios_sim.listar_alertas(estado=estado)
    return {"items": elementos}


@router.post("/alerts/{id_alerta}/ack", response_model=AckResponse)
async def marcar_alerta_como_atendida(id_alerta: int, cuerpo: AckRequest):
    """
    Marca una alerta como 'atendida' (ACK) validando un PIN de demostración.
    """
    if cuerpo.pin != "2131":
        raise HTTPException(status_code=403, detail="PIN inválido")

    resultado = await servicios_sim.atender_alerta(
        id_alerta=id_alerta,
        correo_usuario="operador@sapal.mx",
        nota=cuerpo.nota,
    )
    if not resultado:
        raise HTTPException(status_code=404, detail="Alerta no encontrada o ya atendida")
    return resultado


@router.get("/events/stream")
async def flujo_eventos(request: Request):
    """
    Server-Sent Events (SSE) para “tiempo real”.

    Envía:
      - {'type':'hello', 'payload':{'ts':...}} al conectar.
      - {'type':'tick',  'payload':{'ts':...}} cada intervalo.
      - {'type':'alert', 'payload':{id, sector_id, nivel, tipo, ts}} por alerta.
    """
    async def generador_eventos():
        saludo_inicial = {
            "type": "hello",
            "payload": {"ts": datetime.now(timezone.utc).isoformat()}
        }
        yield f"data: {json.dumps(saludo_inicial)}\n\n"

        async for paquete in servicios_sim.suscribirse_eventos():
            if await request.is_disconnected():
                break
            yield f"data: {json.dumps(paquete)}\n\n"

    return StreamingResponse(
        generador_eventos(),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
        media_type="text/event-stream",
    )