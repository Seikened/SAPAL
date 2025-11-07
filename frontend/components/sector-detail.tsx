"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { X, AlertTriangle, Droplets, Gauge } from "lucide-react"

interface Sector {
  id: string
  name: string
  status: "normal" | "warning" | "critical"
  efficiency: number
  pressure: number
  alerts: string[]
  trend: "up" | "down" | "stable"
}

interface SectorDetailProps {
  sector: Sector
  onClose: () => void
}

export function SectorDetail({ sector, onClose }: SectorDetailProps) {
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 space-y-6">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-bold">{sector.name}</h2>
              <p className="text-sm text-muted-foreground">Detalle del sector</p>
            </div>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Status indicators */}
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Droplets className="h-4 w-4" />
                <span className="text-sm">Eficiencia</span>
              </div>
              <p className="text-2xl font-bold">{sector.efficiency}%</p>
              <p className="text-xs text-muted-foreground">
                {sector.efficiency >= 85 ? "Óptimo" : sector.efficiency >= 70 ? "Aceptable" : "Bajo"}
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Gauge className="h-4 w-4" />
                <span className="text-sm">Presión</span>
              </div>
              <p className="text-2xl font-bold">{sector.pressure} PSI</p>
              <p className="text-xs text-muted-foreground">
                {sector.pressure >= 35 && sector.pressure <= 42 ? "Normal" : "Anómalo"}
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2 text-muted-foreground">
                <AlertTriangle className="h-4 w-4" />
                <span className="text-sm">Alertas</span>
              </div>
              <p className="text-2xl font-bold">{sector.alerts.length}</p>
              <p className="text-xs text-muted-foreground">Activas</p>
            </div>
          </div>

          {/* Alerts */}
          {sector.alerts.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-semibold">Alertas Activas</h3>
              {sector.alerts.map((alert, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 bg-destructive/10 border border-destructive/20 rounded-lg"
                >
                  <AlertTriangle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
                  <p className="text-sm">{alert}</p>
                </div>
              ))}
            </div>
          )}

          {/* Recommendations */}
          <div className="space-y-3">
            <h3 className="font-semibold">Recomendaciones del Sistema</h3>
            <Card className="p-4 bg-primary/5 border-primary/20">
              <div className="space-y-3">
                {sector.status === "critical" && sector.id === "233" && (
                  <>
                    <p className="text-sm leading-relaxed">
                      <strong>Sector 233 con +20% de sobrepresión</strong> respecto a su histórico. Probable
                      transferencia desde Sector 234. Revisar válvula 17.
                    </p>
                    <div className="pt-2 border-t">
                      <p className="text-xs text-muted-foreground mb-2">Impacto estimado:</p>
                      <p className="text-sm">4,800 m³ perdidos/mes → costo energético alto</p>
                    </div>
                    <div className="pt-2 border-t">
                      <p className="text-xs text-muted-foreground mb-2">Siguiente acción:</p>
                      <Badge variant="destructive">Prioridad Alta</Badge>
                      <p className="text-sm mt-2">Inspección en campo en válvula 17. Tiempo sugerido: hoy.</p>
                    </div>
                  </>
                )}

                {sector.status === "warning" && sector.id === "145" && (
                  <>
                    <p className="text-sm leading-relaxed">
                      <strong>Sector 145 estará en disponibilidad baja</strong> mañana entre 14:00-18:00 si no se
                      redistribuye. Consumo esperado por calor: +45%.
                    </p>
                    <div className="pt-2 border-t">
                      <p className="text-xs text-muted-foreground mb-2">Siguiente acción:</p>
                      <Badge variant="outline" className="bg-warning/10 border-warning text-warning">
                        Prioridad Media
                      </Badge>
                      <p className="text-sm mt-2">Programar redistribución desde Sector 144 antes de las 13:00.</p>
                    </div>
                  </>
                )}

                {sector.status === "normal" && (
                  <p className="text-sm leading-relaxed">
                    Sector operando dentro de parámetros normales. Continuar monitoreo rutinario.
                  </p>
                )}
              </div>
            </Card>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <Button variant="outline" className="flex-1 bg-transparent">
              Marcar como Atendida
            </Button>
            <Button variant="default" className="flex-1">
              Escalar a Supervisor
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}
