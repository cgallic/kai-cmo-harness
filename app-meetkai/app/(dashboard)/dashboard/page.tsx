"use client";

import { useState, useCallback } from "react";
import { useBrand, useAudit, useIntegrations, useActions, useSnapshots } from "@/lib/hooks";
import { AuditScoreRing } from "@/components/dashboard/audit-score-ring";
import { ConnectedAccounts } from "@/components/dashboard/connected-accounts";
import { QuickStats } from "@/components/dashboard/quick-stats";
import { PendingActions } from "@/components/dashboard/pending-actions";
import { ActivityFeed } from "@/components/dashboard/activity-feed";
import { Skeleton } from "@/components/ui/skeleton";
import type { Audit } from "@/lib/types";

export default function DashboardPage() {
  const { brand, loading: brandLoading } = useBrand();
  const { audit, loading: auditLoading, setAudit } = useAudit(brand?.id);
  const { integrations } = useIntegrations(brand?.id);
  const { actions } = useActions(brand?.id);
  const { snapshots } = useSnapshots(brand?.id);
  const [auditRunning, setAuditRunning] = useState(false);
  const [auditError, setAuditError] = useState<string | null>(null);

  const runAudit = useCallback(async () => {
    if (!brand?.id || auditRunning) return;
    setAuditRunning(true);
    setAuditError(null);

    try {
      const res = await fetch("/api/audits/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brand_id: brand.id, domain: brand.url }),
      });

      const data = await res.json();

      if (!res.ok) {
        setAuditError(data.error || "Audit failed");
        return;
      }

      // Update local audit state with the returned data
      const newAudit: Audit = {
        id: data.audit_id,
        brand_id: brand.id,
        overall_score: data.overall_score,
        category_scores: data.category_scores || {},
        findings: data.findings || [],
        metadata: {},
        created_at: data.created_at || new Date().toISOString(),
      };
      setAudit(newAudit);
    } catch {
      setAuditError("Network error. Please try again.");
    } finally {
      setAuditRunning(false);
    }
  }, [brand, auditRunning, setAudit]);

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

  // Determine effective audit (from hook or from run)
  const displayAudit = auditLoading ? null : audit;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight">{brand.name}</h1>
        <p className="text-text-secondary text-sm mt-1">{brand.url || "Dashboard overview"}</p>
      </div>

      {/* Quick stats */}
      <QuickStats audit={displayAudit} integrations={integrations} actions={actions} snapshots={snapshots} />

      {/* Audit error */}
      {auditError && (
        <div className="bg-error-dim border border-error/20 rounded-[12px] px-4 py-3 text-sm text-error">
          {auditError}
        </div>
      )}

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AuditScoreRing
          audit={displayAudit}
          brandUrl={brand.url}
          brandId={brand.id}
          running={auditRunning}
          onRunAudit={runAudit}
          onAuditComplete={setAudit}
        />
        <ConnectedAccounts integrations={integrations} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PendingActions actions={actions} />
        <ActivityFeed actions={actions} />
      </div>
    </div>
  );
}
