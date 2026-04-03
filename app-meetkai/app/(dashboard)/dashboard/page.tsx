"use client";

import { useBrand, useAudit, useIntegrations, useActions, useSnapshots } from "@/lib/hooks";
import { AuditScoreRing } from "@/components/dashboard/audit-score-ring";
import { ConnectedAccounts } from "@/components/dashboard/connected-accounts";
import { QuickStats } from "@/components/dashboard/quick-stats";
import { PendingActions } from "@/components/dashboard/pending-actions";
import { ActivityFeed } from "@/components/dashboard/activity-feed";
import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardPage() {
  const { brand, loading: brandLoading } = useBrand();
  const { audit, loading: auditLoading } = useAudit(brand?.id);
  const { integrations } = useIntegrations(brand?.id);
  const { actions } = useActions(brand?.id);
  const { snapshots } = useSnapshots(brand?.id);

  if (brandLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24" />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  if (!brand) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <h2 className="font-display text-2xl font-semibold mb-2">Welcome to MeetKai</h2>
        <p className="text-text-secondary mb-6">Set up your business profile to get started.</p>
        <a href="/settings?onboarding=true" className="inline-flex items-center px-6 py-3 bg-amber text-background font-semibold rounded-[12px] hover:bg-amber-light transition-colors">
          Set up your profile
        </a>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight">{brand.name}</h1>
        <p className="text-text-secondary text-sm mt-1">{brand.url || "Dashboard overview"}</p>
      </div>

      {/* Quick stats */}
      <QuickStats audit={audit} integrations={integrations} actions={actions} snapshots={snapshots} />

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AuditScoreRing audit={audit} />
        <ConnectedAccounts integrations={integrations} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PendingActions actions={actions} />
        <ActivityFeed actions={actions} />
      </div>
    </div>
  );
}
