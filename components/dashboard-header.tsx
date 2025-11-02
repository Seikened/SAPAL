// components/dashboard-header.tsx
import { Card } from "@/components/ui/card";
import { Activity, Clock, Database, AlertTriangle } from "lucide-react";
import { apiGet, KPIResponse } from "@/lib/api";

export async function DashboardHeader() {
  const kpis = await apiGet<KPIResponse>("/sim/kpis/current");
  const fmtPct = (x: number) => `${(x * 100).toFixed(1)}%`;

  const statusEfic = kpis.eficiencia >= 0.85 ? "success" : kpis.eficiencia >= 0.75 ? "warning" : "destructive";
  const statusUso = kpis.uso_datos_pct >= 0.7 ? "success" : "warning";
  const statusRiesgo = kpis.sectores_en_riesgo > 5 ? "destructive" : kpis.sectores_en_riesgo > 0 ? "warning" : "success";
  const color = (s: "success" | "warning" | "destructive") =>
    s === "success" ? "text-success" : s === "warning" ? "text-warning" : "text-destructive";

  return (
    <header className="sticky top-0 z-50 border-b bg-card shadow-sm">
      <div className="container mx-auto px-4 py-4">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h1 className="font-heading text-2xl font-semibold tracking-tight text-foreground">
              Sistema de Agua Potable - León
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">Dashboard Operativo</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-muted-foreground uppercase tracking-wide">Última actualización</p>
            <p className="text-sm font-medium tabular-nums mt-0.5">
              {new Date(kpis.ts).toLocaleTimeString("es-MX")}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Eficiencia Actual</p>
                <p className={`text-3xl font-bold tabular-nums leading-none ${color(statusEfic)}`}>
                  {fmtPct(kpis.eficiencia)}
                </p>
                <p className="text-xs text-muted-foreground mt-2">Inyección / Consumo</p>
              </div>
              <Activity className={`h-8 w-8 ${color(statusEfic)}`} />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Tiempo de Decisión</p>
                <p className={`text-3xl font-bold tabular-nums leading-none text-success`}>
                  {kpis.tiempo_decision_min} min
                </p>
                <p className="text-xs text-muted-foreground mt-2">Promedio últimas 24h</p>
              </div>
              <Clock className={`h-8 w-8 text-success`} />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Uso de Datos</p>
                <p className={`text-3xl font-bold tabular-nums leading-none ${color(statusUso)}`}>
                  {fmtPct(kpis.uso_datos_pct)}
                </p>
                <p className="text-xs text-muted-foreground mt-2">Decisiones basadas en datos</p>
              </div>
              <Database className={`h-8 w-8 ${color(statusUso)}`} />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Sectores en Riesgo</p>
                <p className={`text-3xl font-bold tabular-nums leading-none ${color(statusRiesgo)}`}>
                  {kpis.sectores_en_riesgo}
                </p>
                <p className="text-xs text-muted-foreground mt-2">Requieren atención</p>
              </div>
              <AlertTriangle className={`h-8 w-8 ${color(statusRiesgo)}`} />
            </div>
          </Card>
        </div>
      </div>
    </header>
  );
}