// components/dashboard-header.tsx
"use client";
import { Card } from "@/components/ui/card";
import { Activity, Clock, AlertTriangle, TrendingUp, TrendingDown } from "lucide-react";
import type { KPIResponse } from "@/lib/api";
import { usePoll } from "@/hooks/use-poll";
import { Sparkline } from "@/components/sparkline";

export function DashboardHeader() {
  const { data: kpis } = usePoll<KPIResponse>("/sim/kpis/current", 10_000);
  if (!kpis) return null;

  const fmtPct = (x: number) => `${(x * 100).toFixed(1)}%`;
  const statusEfic =
    kpis.eficiencia >= 0.85 ? "text-success" :
    kpis.eficiencia >= 0.75 ? "text-warning" :
    "text-destructive";

  const trend = Array.isArray(kpis.eficiencia_trend) ? kpis.eficiencia_trend : [];
  const delta = trend.length > 1 ? trend.at(-1)! - trend.at(-2)! : 0;

  const trendIcon =
    delta > 0.0005 ? <TrendingUp className="h-4 w-4 inline align-middle" /> :
    delta < -0.0005 ? <TrendingDown className="h-4 w-4 inline align-middle" /> :
    null;

  const riesgosClass =
    kpis.sectores_en_riesgo > 5 ? "text-destructive" :
    kpis.sectores_en_riesgo > 0 ? "text-warning" : "text-success";

  return (
    <header className="sticky top-0 z-50 border-b bg-card/80 backdrop-blur supports-[backdrop-filter]:bg-card/60 shadow-sm">
      <div className="container mx-auto px-4 py-4">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h1 className="font-heading text-2xl font-semibold tracking-tight text-foreground">Sistema de Agua Potable - León</h1>
            <p className="text-sm text-muted-foreground mt-0.5">Dashboard Operativo</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-muted-foreground uppercase tracking-wide">Última actualización</p>

            <p className="text-sm font-medium tabular-nums mt-0.5">{new Date(kpis.ts).toLocaleTimeString("es-MX" )}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="p-4">
            <div className="flex items-start justify-between">
              <div className="min-w-0">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Eficiencia Global</p>
                <p className={`text-3xl font-bold tabular-nums leading-none ${statusEfic}`}>
                  {fmtPct(kpis.eficiencia)}{" "}
                  <span className="text-sm font-medium text-muted-foreground align-middle">
                    {trendIcon}
                    {delta === 0 ? " Estable" : ` ${delta > 0 ? "+" : ""}${(delta * 100).toFixed(1)} pts`}
                  </span>
                </p>
                <div className="mt-2 text-muted-foreground">
                  <Sparkline data={trend} className={`${statusEfic}`} />
                </div>
                <p className="text-xs text-muted-foreground mt-1">Consumo / Inyección (promedio por tick)</p>
              </div>
              <Activity className={`h-8 w-8 ${statusEfic}`} />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Tiempo de Decisión</p>
                <p className="text-3xl font-bold tabular-nums leading-none text-success">{kpis.tiempo_decision_min} min</p>
                <p className="text-xs text-muted-foreground mt-2">Promedio últimas 24h</p>
              </div>
              <Clock className="h-8 w-8 text-success" />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Alertas</p>
                <p className={`text-3xl font-bold tabular-nums leading-none ${riesgosClass}`}>
                  {kpis.sectores_en_riesgo} <span className="text-base font-medium text-muted-foreground">sectores en riesgo</span>
                </p>
                <p className="text-xs text-muted-foreground mt-2">Atendidas (24h): <span className="font-medium text-foreground">{kpis.alertas_atendidas_24h}</span></p>
              </div>
              <AlertTriangle className={`h-8 w-8 ${riesgosClass}`} />
            </div>
          </Card>
        </div>
      </div>
    </header>
  );
}