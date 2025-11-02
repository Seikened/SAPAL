// components/sector-grid.tsx
"use client";
import { useState, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SectorDetail } from "@/components/sector-detail";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { SectorsResponse, SectorItem } from "@/lib/api";
import { usePoll } from "@/hooks/use-poll";

type SectorStatus = "normal" | "warning" | "critical";

export function SectorGrid() {
  const data = usePoll<SectorsResponse>("/sim/sectors", 10_000);
  const sectors = data?.items ?? [];
  const [selected, setSelected] = useState<SectorItem | null>(null);

  const mapped = useMemo(() => {
    return sectors.map((s) => {
      let status: SectorStatus = "normal";
      if (s.estado === "alerta") status = "warning";
      if (s.estado === "critico") status = "critical";
      const trend =
        s.tendencia.length >= 2
          ? s.tendencia[s.tendencia.length - 1] > s.tendencia[0]
            ? "up"
            : s.tendencia[s.tendencia.length - 1] < s.tendencia[0]
            ? "down"
            : "stable"
          : "stable";
      return { ...s, status, trend };
    });
  }, [sectors]);

  const getStatusColor = (status: SectorStatus) =>
    status === "normal"
      ? "bg-success/10 border-success text-success"
      : status === "warning"
      ? "bg-warning/10 border-warning text-warning"
      : "bg-destructive/10 border-destructive text-destructive";

  const getStatusLabel = (status: SectorStatus) =>
    status === "normal" ? "Normal" : status === "warning" ? "Alerta" : "Crítico";

  const getTrendIcon = (trend: "up" | "down" | "stable") =>
    trend === "up" ? <TrendingUp className="h-4 w-4" /> : trend === "down" ? <TrendingDown className="h-4 w-4" /> : <Minus className="h-4 w-4" />;

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
          {mapped.map((sector) => (
            <Card
              key={sector.id}
              className={`p-4 cursor-pointer transition-all hover:shadow-md border-2 ${getStatusColor(sector.status)}`}
              onClick={() => setSelected(sector)}
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-heading font-semibold text-sm tracking-tight">{sector.nombre}</p>
                    <p className="text-xs opacity-80 font-medium">{getStatusLabel(sector.status)}</p>
                  </div>
                  {getTrendIcon(sector.trend)}
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="opacity-80">Eficiencia</span>
                    <span className="font-medium tabular-nums">{Math.round(sector.eficiencia * 100)}%</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="opacity-80">Presión</span>
                    <span className="font-medium tabular-nums">{sector.presion_psi} PSI</span>
                  </div>
                </div>

                {sector.alertas_abiertas > 0 && (
                  <div className="pt-2 border-t border-current/20">
                    <p className="text-xs font-medium tabular-nums">{sector.alertas_abiertas} alerta(s)</p>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      </div>

      {selected && (
        <SectorDetail
          sector={{
            id: String(selected.id),
            name: selected.nombre,
            status: selected.estado === "critico" ? "critical" : selected.estado === "alerta" ? "warning" : "normal",
            efficiency: Math.round(selected.eficiencia * 100),
            pressure: selected.presion_psi,
            alerts: selected.alertas_abiertas > 0 ? ["Alertas activas en este sector"] : [],
            trend: "stable",
          }}
          onClose={() => setSelected(null)}
        />
      )}
    </>
  );
}
