// components/alerts-panel.tsx
"use client";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, TrendingUp, Droplets, Clock } from "lucide-react";
import type { AlertsResponse, AlertItem } from "@/lib/api";
import { usePoll } from "@/hooks/use-poll";
import { ackAlert } from "@/lib/api";
import { useState } from "react";

const iconFor = (tipo?: string) => {
  if (tipo === "no_facturable") return Droplets;
  if (tipo === "sobrepresion") return AlertTriangle;
  return TrendingUp;
};

export function AlertsPanel() {
  const data = usePoll<AlertsResponse>("/sim/alerts?estado=abierta", 10_000);
  const items = data?.items ?? [];
  const [working, setWorking] = useState<number | null>(null);

  const getPriority = (nivel: AlertItem["nivel"]) => (nivel === "alta" ? "destructive" : nivel === "media" ? "outline" : "secondary");
  const getLabel = (nivel: AlertItem["nivel"]) => (nivel === "alta" ? "Alta" : nivel === "media" ? "Media" : "Baja");

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <h2 className="font-heading text-xl font-semibold tracking-tight">Alertas Prioritarias</h2>
        <div className="space-y-3">
          {items.map((a) => {
            const Icon = iconFor(a.explicacion && (a as any).tipo);
            return (
              <Card key={a.id} className="p-4 space-y-3">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-heading text-base font-semibold leading-tight tracking-tight">{a.titulo}</h3>
                      <Badge variant={getPriority(a.nivel)} className="shrink-0 text-xs font-medium">
                        {getLabel(a.nivel)}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground leading-relaxed">{a.resumen}</p>

                    <div className="pt-2 border-t space-y-2">
                      {a.impacto_m3_mes && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                            Impacto estimado:
                          </p>
                          <p className="text-sm leading-relaxed">{a.impacto_m3_mes.toLocaleString("es-MX")} m³/mes</p>
                        </div>
                      )}
                      <div>
                        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                          Siguiente acción:
                        </p>
                        <p className="text-sm leading-relaxed">{a.recomendacion}</p>
                      </div>
                    </div>

                    <div className="flex gap-2 pt-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 bg-transparent font-medium"
                        disabled={working === a.id}
                        onClick={async () => {
                          try {
                            setWorking(a.id);
                            await ackAlert(a.id, "2131", "Atendida desde UI");
                          } finally {
                            setWorking(null);
                          }
                        }}
                      >
                        Atendida
                      </Button>
                      <Button size="sm" variant="default" className="flex-1 font-medium">
                        Escalar
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
          {items.length === 0 && <Card className="p-4 text-sm text-muted-foreground">Sin alertas abiertas ahora mismo.</Card>}
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="font-heading text-xl font-semibold tracking-tight">Predicción a Corto Plazo</h2>
        <Card className="p-4 space-y-3 bg-accent/50">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Clock className="h-5 w-5 text-primary" />
            </div>
            <div className="flex-1 space-y-2">
              <h3 className="font-heading text-base font-semibold leading-tight tracking-tight">
                Predicción demo: variabilidad por calor
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                La demanda subirá en horas cálidas; monitorea sectores con pérdidas históricas altas.
              </p>
              <div className="flex items-center gap-2 pt-1">
                <Badge variant="outline" className="text-xs font-medium">
                  Próximas 48h
                </Badge>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
