// components/sector-grid.tsx
"use client";
import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SectorDetail } from "@/components/sector-detail";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { apiGet, SectorsResponse } from "@/lib/api";

type SectorStatus = "normal" | "warning" | "critical";
type Trend = "up" | "down" | "stable";

function estadoToStatus(e: "normal" | "alerta" | "critico"): SectorStatus {
  if (e === "alerta") return "warning";
  if (e === "critico") return "critical";
  return "normal";
}
function tendenciaToTrend(vals: number[]): Trend {
  if (vals.length < 2) return "stable";
  const first = vals[0], last = vals[vals.length - 1];
  if (last > first * 1.02) return "up";
  if (last < first * 0.98) return "down";
  return "stable";
}

interface UISector {
  id: string;
  name: string;
  status: SectorStatus;
  efficiency: number;
  pressure: number;
  alerts: string[];
  trend: Trend;
}

export function SectorGrid() {
  const [selectedSector, setSelectedSector] = useState<UISector | null>(null);
  const [sectors, setSectors] = useState<UISector[]>([]);

  useEffect(() => {
    let alive = true;
    apiGet<SectorsResponse>("/sim/sectors").then(({ items }) => {
      if (!alive) return;
      const mapped = items.map((s) => ({
        id: String(s.id),
        name: s.nombre,
        status: estadoToStatus(s.estado),
        efficiency: Math.round(s.eficiencia * 100),
        pressure: Number(s.presion_psi.toFixed(0)),
        alerts: s.alertas_abiertas ? [`${s.alertas_abiertas} alerta(s)`] : [],
        trend: tendenciaToTrend(s.tendencia ?? []),
      }));
      setSectors(mapped);
    }).catch(console.error);
    return () => { alive = false; };
  }, []);

  const color = (status: SectorStatus) =>
    status === "normal"
      ? "bg-success/10 border-success text-success"
      : status === "warning"
      ? "bg-warning/10 border-warning text-warning"
      : "bg-destructive/10 border-destructive text-destructive";

  const icon = (t: Trend) =>
    t === "up" ? <TrendingUp className="h-4 w-4" /> : t === "down" ? <TrendingDown className="h-4 w-4" /> : <Minus className="h-4 w-4" />;

  return (
    <>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-xl font-semibold tracking-tight">Mapa de Sectores</h2>
          <div className="flex gap-2">
            <Badge variant="outline" className="bg-success/10 border-success text-success text-xs font-medium">Normal</Badge>
            <Badge variant="outline" className="bg-warning/10 border-warning text-warning text-xs font-medium">Alerta</Badge>
            <Badge variant="outline" className="bg-destructive/10 border-destructive text-destructive text-xs font-medium">Crítico</Badge>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {sectors.map((sector) => (
            <Card
              key={sector.id}
              className={`p-4 cursor-pointer transition-all hover:shadow-md border-2 ${color(sector.status)}`}
              onClick={() => setSelectedSector(sector)}
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-heading font-semibold text-sm tracking-tight">{sector.name}</p>
                    <p className="text-xs opacity-80 font-medium">
                      {sector.status === "normal" ? "Normal" : sector.status === "warning" ? "Alerta" : "Crítico"}
                    </p>
                  </div>
                  {icon(sector.trend)}
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="opacity-80">Eficiencia</span>
                    <span className="font-medium tabular-nums">{sector.efficiency}%</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="opacity-80">Presión</span>
                    <span className="font-medium tabular-nums">{sector.pressure} PSI</span>
                  </div>
                </div>

                {sector.alerts.length > 0 && (
                  <div className="pt-2 border-t border-current/20">
                    <p className="text-xs font-medium tabular-nums">{sector.alerts.join(", ")}</p>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      </div>

      {selectedSector && <SectorDetail sector={selectedSector} onClose={() => setSelectedSector(null)} />}
    </>
  );
}