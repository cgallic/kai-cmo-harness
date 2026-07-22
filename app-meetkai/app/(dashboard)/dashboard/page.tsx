"use client";

import { useState, useCallback } from "react";
import { useBrand, useAudit, useIntegrations, useActions, useSnapshots, useAgentRuns } from "@/lib/hooks";
import { QuickStats } from "@/components/dashboard/quick-stats";
import { AttentionItems } from "@/components/dashboard/attention-items";
import { AIActivity } from "@/components/dashboard/ai-activity";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { PendingActions } from "@/components/dashboard/pending-actions";
import { AutopilotCommandCenter } from "@/components/dashboard/autopilot-command-center";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { cn, scoreColor } from "@/lib/utils";
import { Search, Sparkles } from "lucide-react";
import type { Audit } from "@/lib/types";

export default function DashboardPage() {
  const { brand, loading: brandLoading } = useBrand();
  const { audit, loading: auditLoading, setAudit, refresh: refreshAudit } = useAudit(brand?.id);
  const { integrations } = useIntegrations(brand?.id);
  const { actions, refresh: refreshActions } = useActions(brand?.id);
  const { snapshots } = useSnapshots(brand?.id);
  const { runs, loading: runsLoading } = useAgentRuns(brand?.id);
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

  const [generating, setGenerating] = useState(false);
  const handleGenerate = useCallback(async () => {
    if (!brand?.id) return;
    setGenerating(true);
    try {
      await fetch("/api/actions/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brand_id: brand.id, source: "audit" }),
      });
      await refreshActions();
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
        <h2 className="font-display text-2xl font-semibold mb-2">Build the workspace profile first</h2>
        <p className="text-text-secondary mb-6">Kai needs the business, channels, and operating defaults before it can score or propose work.</p>
        <a href="/settings?onboarding=true" className="inline-flex items-center px-6 py-3 bg-amber text-background font-semibold rounded-lg hover:bg-amber-light transition-colors">
          Set up your profile
        </a>
      </div>
    );
  }

  const displayAudit = auditLoading ? null : audit;
  const score = displayAudit?.overall_score;

  return (
    <div className="space-y-6">
      <AutopilotCommandCenter />

      {/* Hero: Score + Brand + Actions */}
      <div className="card flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div className="flex items-center gap-4 flex-1">
          {/* Score ring */}
          <div className="relative w-16 h-16 flex-shrink-0">
            <svg viewBox="0 0 36 36" className="w-16 h-16 -rotate-90">
              <path
                d="M18 2.0845a 15.9155 15.9155 0 0 1 0 31.831a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#1e1e1e"
                strokeWidth="3"
              />
              {score != null && (
                <path
                  d="M18 2.0845a 15.9155 15.9155 0 0 1 0 31.831a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke={score >= 70 ? "#22c55e" : score >= 40 ? "#f59e0b" : "#ef4444"}
                  strokeWidth="3"
                  strokeDasharray={`${score}, 100`}
                  strokeLinecap="round"
                />
              )}
            </svg>
            <span className={cn(
              "absolute inset-0 flex items-center justify-center font-mono text-lg font-bold",
              score != null ? scoreColor(score) : "text-text-tertiary"
            )}>
              {score != null ? Math.round(score) : "—"}
            </span>
          </div>
          <div>
            <h1 className="font-display text-xl font-bold tracking-tight">{brand.name}</h1>
            <p className="text-text-secondary text-sm">{brand.url || "No website set"}</p>
            {score != null && (
              <p className="text-xs text-text-tertiary mt-0.5">Marketing health score</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={runAudit} loading={auditRunning}>
            <Search className="w-3.5 h-3.5" />
            Run Audit
          </Button>
          {audit && actions.filter((a) => a.approval_state === "pending").length === 0 && (
            <Button variant="primary" size="sm" onClick={handleGenerate} loading={generating}>
              <Sparkles className="w-3.5 h-3.5" />
              Draft Actions
            </Button>
          )}
        </div>
      </div>

      {auditError && (
        <div className="bg-error-dim border border-error/20 rounded-lg px-4 py-3 text-sm text-error">
          {auditError}
        </div>
      )}

      <QuickStats audit={displayAudit} integrations={integrations} actions={actions} snapshots={snapshots} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AttentionItems actions={actions} integrations={integrations} />
        <AIActivity runs={runs} loading={runsLoading} />
      </div>

      <QuickActions />

      <PendingActions actions={actions} />
    </div>
  );
}
