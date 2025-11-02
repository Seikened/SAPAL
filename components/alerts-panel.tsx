// components/alerts-panel.tsx
"use client";
import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, TrendingUp, Droplets, Clock } from "lucide-react";
import { apiGet, AlertsResponse, AlertItem, ackAlert } from "@/lib/api";

export function AlertsPanel() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  useEffect(() => {
    let alive = true;
    apiGet<AlertsResponse>("/sim/alerts?estado=abierta").then(({ items }) => {
      if (alive) setAlerts(items);
    }).catch(console.error);
    return () => { alive = false; };
  }, []);

  const iconFor = (tipo?: string) =>
    tipo === "no_facturable" ? Droplets : tipo === "baja_eficiencia" ? AlertTriangle : TrendingUp;

  const onAck = async (id: number) => {
    await ackAlert(id, "2131", "Atendida desde UI");
    setAlerts((prev) => prev.filter(a => a.id !== id));
  };

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <h2 className="font-heading text-xl font-semibold tracking-tight">Alertas Prioritarias</h2>
        <div className="space-y-3">
          {alerts.map((alert) => {
            const Icon = iconFor(alert?.explicacion && (alert.explicacion as any).caracteristica);
            const prioridad = alert.nivel === "alta" ? "destructive" : alert.nivel === "media" ? "outline" : "secondary";
            const label = alert.nivel === "alta" ? "Alta" : alert.nivel === "media" ? "Media" : "Baja";
            return (
              <Card key={alert.id} className="p-4 space-y-3">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-heading text-base font-semibold leading-tight tracking-tight">
                        {alert.titulo}
                      </h3>
                      <Badge variant={prioridad as any} className="shrink-0 text-xs font-medium">
                        {label}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground leading-relaxed">{alert.resumen}</p>

                    <div className="pt-2 border-t space-y-2">
                      {alert.impacto_m3_mes != null && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                            Impacto estimado:
                          </p>
                          <p className="text-sm leading-relaxed">
                            {alert.impacto_m3_mes.toLocaleString("es-MX")} m³/mes
                          </p>
                        </div>
                      )}
                      <div>
                        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                          Siguiente acción:
                        </p>
                        <p className="text-sm leading-relaxed">{alert.recomendacion}</p>
                      </div>
                    </div>

                    <div className="flex gap-2 pt-2">
                      <Button size="sm" variant="outline" className="flex-1 bg-transparent font-medium" onClick={() => onAck(alert.id)}>
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
          {alerts.length === 0 && (
            <Card className="p-4 space-y-2 bg-accent/30">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-primary/10">
                  <Clock className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="font-heading text-base font-semibold leading-tight tracking-tight">
                    Sin alertas abiertas
                  </h3>
                  <p className="text-sm text-muted-foreground">Buen momento para mantenimiento preventivo.</p>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}