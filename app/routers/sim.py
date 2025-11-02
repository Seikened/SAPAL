# app/routers/sim.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from ..db import get_session
from ..schemas import KPIResponse, SectorsResponse, AlertsResponse, AckRequest, AckResponse, AlertRead, SectorCard
from ..services import sim as svc
from datetime import datetime, timezone
import json
import asyncio

router = APIRouter()

@router.get("/kpis/current", response_model=KPIResponse)
def kpis_current():
    data = svc.compute_kpis()
    return dict(
        ts=data["ts"],
        eficiencia=round(data["eficiencia"], 3),
        tiempo_decision_min=data["tiempo_decision_min"],
        uso_datos_pct=round(data["uso_datos_pct"], 2),
        sectores_en_riesgo=data["sectores_en_riesgo"],
    )

@router.get("/sectors", response_model=SectorsResponse)
def sectors():
    items = svc.sectors_grid()
    return {"items": items}

@router.get("/alerts", response_model=AlertsResponse)
def alerts(status: str = "abierta"):
    items = svc.list_alerts(status=status)
    return {"items": items}

@router.post("/alerts/{alert_id}/ack", response_model=AckResponse)
def alerts_ack(alert_id: int, body: AckRequest):
    # validación mínima de PIN para demo
    if body.pin != "123456":
        raise HTTPException(status_code=403, detail="PIN inválido")
    res = svc.acknowledge_alert(alert_id, user_email="operador@sapal.mx", nota=body.nota)
    if not res:
        raise HTTPException(status_code=404, detail="Alerta no encontrada o ya atendida")
    return res

@router.get("/events/stream")
async def events_stream(request: Request):
    async def event_generator():
        # primer “hola” para enganchar
        yield f"data: {json.dumps({'type':'hello','payload':{'ts':datetime.now(timezone.utc).isoformat()}})}\n\n"
        async for payload in svc.subscribe():
            if await request.is_disconnected():
                break
            yield f"data: {json.dumps(payload)}\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "text/event-stream",
        "Connection": "keep-alive",
    }
    return StreamingResponse(event_generator(), headers=headers)