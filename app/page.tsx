import { DashboardHeader } from "@/components/dashboard-header"
import { SectorGrid } from "@/components/sector-grid"
import { AlertsPanel } from "@/components/alerts-panel"
import { AssistantButton } from "@/components/assistant-button"

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Fixed header with global KPIs */}
      <DashboardHeader />

      {/* Main content area */}
      <main className="container mx-auto p-4 pt-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left panel: Sector grid/map */}
          <div className="lg:col-span-2">
            <SectorGrid />
          </div>

          {/* Right panel: Alerts and predictions */}
          <div className="lg:col-span-1">
            <AlertsPanel />
          </div>
        </div>
      </main>

      {/* Floating AI assistant button */}
      <AssistantButton />
    </div>
  )
}
