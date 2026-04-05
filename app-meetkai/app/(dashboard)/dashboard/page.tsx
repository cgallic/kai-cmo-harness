"use client";

import { useState, useCallback } from "react";
import { useBrand, useAudit, useIntegrations, useActions, useSnapshots } from "@/lib/hooks";
import { AuditScoreRing } from "@/components/dashboard/audit-score-ring";
import { ConnectedAccounts } from "@/components/dashboard/connected-accounts";
import { QuickStats } from "@/components/dashboard/quick-stats";
import { PendingActions } from "@/components/dashboard/pending-actions";
import { ActivityFeed } from "@/components/dashboard/activity-feed";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Sparkles } from "lucide-react";

export default function DashboardPage() {
  const { brand, loading: brandLoading } = useBrand();
  const { audit, loading: auditLoading } = useAudit(brand?.id);
  const { integrations } = useIntegrations(brand?.id);
  const { actions, refresh: refreshActions } = useActions(brand?.id);
  const { snapshots } = useSnapshots(brand?.id);

  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);

  const hasAudit = !!audit;
  const hasActions = actions.length > 0;
  const showGeneratePrompt = hasAudit && !hasActions && !auditLoading;

  const handleGenerate = useCallback(async () => {
    if (!brand?.id) return;
    setGenerating(true);
    setGenerateError(null);

    try {
      const res = await fetch("/api/actions/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brand_id: brand.id, source: "audit" }),
      });

      const data = await res.json();

      if (!res.ok) {
        setGenerateError(data.error || "Failed to generate actions");
        return;
      }

      await refreshActions();
    } catch {
      setGenerateError("Network error. Please try again.");
    } finally {
      setGenerating(false);
    }
  }, [brand?.id, refreshActions]);

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

      {/* Generate actions prompt */}
      {showGeneratePrompt && (
        <div className="bg-amber-dim/50 border border-amber/20 rounded-[12px] p-5 flex items-center gap-4">
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-foreground mb-1">
              Audit complete — generate recommended actions?
            </h3>
            <p className="text-xs text-text-secondary">
              MiKai found findings in your audit. Generate action proposals to start fixing issues.
            </p>
            {generateError && (
              <p className="text-xs text-error mt-1">{generateError}</p>
            )}
          </div>
          <Button
            variant="primary"
            size="md"
            onClick={handleGenerate}
            loading={generating}
          >
            <Sparkles className="w-4 h-4" />
            Generate Actions
          </Button>
        </div>
      )}

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
