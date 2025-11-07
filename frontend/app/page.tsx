// app/page.tsx
import { DashboardHeader } from "@/components/dashboard-header";
import { SectorGrid } from "@/components/sector-grid";
import { AlertsPanel } from "@/components/alerts-panel";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader />
      <main className="container mx-auto p-4 pt-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <SectorGrid />
          </div>
          <div className="lg:col-span-1">
            <AlertsPanel />
          </div>
        </div>
      </main>
    </div>
  );
}