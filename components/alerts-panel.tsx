// components/alerts-panel.tsx
"use client";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, TrendingUp, Droplets, Clock } from "lucide-react";
import type { AlertsResponse, AlertItem } from "@/lib/api";
import { usePoll } from "@/hooks/use-poll";
import { ackAlert } from "@/lib/api";
import { useEffect, useMemo, useState } from "react";

const iconFor = (tipo?: string) => {
  if (tipo === "no_facturable") return Droplets;
  if (tipo === "sobrepresion") return AlertTriangle;
  return TrendingUp; // baja_eficiencia o fallback
};

export function AlertsPanel() {
  const { data, refetch, setData } = usePoll<AlertsResponse>("/sim/alerts?estado=abierta", 10_000);
  const serverItems = data?.items ?? [];
  const [items, setItems] = useState<AlertItem[]>(serverItems);
  const [working, setWorking] = useState<number | null>(null);

  // sincroniza cuando el servidor trae una nueva foto
  useEffect(() => {
    setItems(serverItems);
  }, [serverItems]);

  const sorted = useMemo(
    () =>
      [...items].sort((a, b) => {
        const p = (x: AlertItem) => (x.nivel === "alta" ? 2 : x.nivel === "media" ? 1 : 0);
        const d = p(b) - p(a);
        return d !== 0 ? d : new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }),
    [items]
  );

  const getPriority = (nivel: AlertItem["nivel"]) =>
    nivel === "alta" ? "destructive" : nivel === "media" ? "outline" : "secondary";
  const getLabel = (nivel: AlertItem["nivel"]) =>
    nivel === "alta" ? "Alta" : nivel === "media" ? "Media" : "Baja";

  async function onAck(a: AlertItem) {
    try {
      setWorking(a.id);
      // optimista: quita de UI ya
      setItems((prev) => prev.filter((x) => x.id !== a.id));
      // también actualiza el snapshot del hook para que no “reviva” antes del próximo poll
      setData((prev) => (prev ? { ...prev, items: prev.items.filter((x) => x.id !== a.id) } : prev));
      // call
      await ackAlert(a.id, "2131", "Atendida desde UI");
      // resíncora desde el servidor por si hubo carreras
      await refetch();
    } catch {
      // si falló, vuelve a insertarla
      setItems((prev) => [...prev, a]);
      await refetch();
    } finally {
      setWorking(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <h2 className="font-heading text-xl font-semibold tracking-tight">**Alertas Prioritarias**</h2>
        <div className="space-y-3">
          {sorted.map((a) => {
            const Icon = iconFor(a.tipo);
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
                            **Impacto estimado**
                          </p>
                          <p className="text-sm leading-relaxed">{a.impacto_m3_mes.toLocaleString("es-MX")} m³/mes</p>
                        </div>
                      )}
                      <div>
                        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                          **Siguiente acción**
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
                        onClick={() => onAck(a)}
                      >
                        {working === a.id ? "Atendiendo..." : "Atendida"}
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
          {sorted.length === 0 && (
            <Card className="p-4 text-sm text-muted-foreground">Sin alertas abiertas ahora mismo.</Card>
          )}
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="font-heading text-xl font-semibold tracking-tight">**Predicción a Corto Plazo**</h2>
        <Card className="p-4 space-y-3 bg-accent/50">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Clock className="h-5 w-5 text-primary" />
            </div>
            <div className="flex-1 space-y-2">
              <h3 className="font-heading text-base font-semibold leading-tight tracking-tight">
                **Predicción demo: variabilidad por calor**
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