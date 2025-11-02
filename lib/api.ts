// lib/api.ts
export const API = process.env.NEXT_PUBLIC_API_URL ?? "";

export type KPIResponse = {
  ts: string;                         // ISO
  eficiencia: number;                 // 0..1
  eficiencia_trend: number[];         // últimos puntos (0..1) ordenados por tiempo asc
  sectores_en_riesgo: number;         // sectores con alertas abiertas
  alertas_atendidas_24h: number;      // cuántas se atendieron en las últimas 24h
  tiempo_decision_min: number;        // como ya lo tenías
};

export type SectorItem = {
  id: number;
  nombre: string;
  estado: "normal" | "alerta" | "critico";
  eficiencia: number;
  presion_psi: number;
  alertas_abiertas: number;
  tendencia: number[];
};
export type SectorsResponse = { items: SectorItem[] };

export type AlertItem = {
  id: number;
  nivel: "alta" | "media" | "baja";
  tipo: "no_facturable" | "baja_eficiencia" | "sobrepresion" | string; // backend-safe
  titulo: string;
  resumen: string;
  impacto_m3_mes: number | null;
  recomendacion: string;
  sector_id: number;
  created_at: string;
  estado: "abierta" | "atendida" | "escalada";
  explicacion: Record<string, unknown> | null;
};
export type AlertsResponse = { items: AlertItem[] };

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path.startsWith("http") ? path : `${API}${path}`, {
    cache: "no-store",
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export async function ackAlert(id: number, pin = "2131", nota?: string) {
  const res = await fetch(`${API}/sim/alerts/${id}/ack`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pin, nota }),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}