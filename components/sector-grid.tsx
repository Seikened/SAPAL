// components/sector-grid.tsx
"use client";
import { useState, useMemo } from "react";
import { Badge } from "@/components/ui/badge";
import { SectorDetail } from "@/components/sector-detail";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { SectorsResponse, SectorItem } from "@/lib/api";
import { usePoll } from "@/hooks/use-poll";
import { AnimatedCard } from "@/components/ui/animated-card";

type VisualLevel = "normal" | "warning" | "critical";

export function SectorGrid() {
  const { data } = usePoll<SectorsResponse>("/sim/sectors", 10_000);
  const sectors = data?.items ?? [];
  const [selected, setSelected] = useState<SectorItem | null>(null);

  const mapped = useMemo(() => {
    return sectors.map((s) => {
      const serie = Array.isArray(s.tendencia) ? s.tendencia : [];
      const trend =
        serie.length >= 2
          ? serie.at(-1)! > serie[0] ? "up" :
            serie.at(-1)! < serie[0] ? "down" : "stable"
          : "stable";
      const level: VisualLevel =
        s.estado === "critico" ? "critical" :
        s.estado === "alerta" ? "warning" : "normal";
      return { ...s, trend, level };
    });
  }, [sectors]);

  const statusChip = (level: VisualLevel) =>
    level === "normal"
      ? <Badge variant="outline" className="bg-success/10 border-success text-success text-xs font-medium">Normal</Badge>
      : level === "warning"
      ? <Badge variant="outline" className="bg-warning/10 border-warning text-warning text-xs font-medium">Alerta</Badge>
      : <Badge variant="outline" className="bg-destructive/10 border-destructive text-destructive text-xs font-medium">Crítico</Badge>;

  const cardChromeClasses = (level: VisualLevel) =>
    level === "normal"
      ? "border-success/40 hover:border-success bg-success/5"
      : level === "warning"
      ? "border-warning/70 hover:border-warning bg-warning/10"
      : "border-destructive/80 hover:border-destructive bg-destructive/10";

  const getTrendIcon = (trend: "up" | "down" | "stable") =>
    trend === "up" ? <TrendingUp className="h-4 w-4 opacity-80" /> :
    trend === "down" ? <TrendingDown className="h-4 w-4 opacity-80" /> :
    <Minus className="h-4 w-4 opacity-60" />;

  return (
    <>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-xl font-semibold tracking-tight">**Mapa de Sectores**</h2>
          <div className="flex gap-2">
            <Badge variant="outline" className="bg-success/10 border-success text-success text-xs font-medium">Normal</Badge>
            <Badge variant="outline" className="bg-warning/10 border-warning text-warning text-xs font-medium">Alerta</Badge>
            <Badge variant="outline" className="bg-destructive/10 border-destructive text-destructive text-xs font-medium">Crítico</Badge>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {mapped.map((sector) => (
            <AnimatedCard
              key={sector.id}
              level={sector.level}
              aria-label={`Sector ${sector.nombre} estado ${sector.level}`}
              className={`border-2 rounded-2xl ${cardChromeClasses(sector.level)}`}
              onClick={() => setSelected(sector)}
            >
              <div className="p-4 space-y-2">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-heading font-semibold text-sm tracking-tight">{sector.nombre}</p>
                    <div className="mt-1">{statusChip(sector.level)}</div>
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
            </AnimatedCard>
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