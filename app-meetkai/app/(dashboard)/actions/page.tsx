"use client";

import { useState, useCallback } from "react";
import { useBrand, useActions, useAudit } from "@/lib/hooks";
import { Tabs } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge, RiskBadge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { createClient } from "@/lib/supabase/client";
import { cn, timeAgo } from "@/lib/utils";
import type { Action } from "@/lib/types";
import { Check, X, Clock, ChevronDown, ChevronUp, Zap, Sparkles, Play } from "lucide-react";

export default function ActionsPage() {
  const { brand, loading: brandLoading } = useBrand();
  const { actions, loading: actionsLoading, refresh } = useActions(brand?.id);
  const { audit } = useAudit(brand?.id);
  const [activeTab, setActiveTab] = useState("pending");
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);

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

      // Refresh actions list — realtime subscription will also catch it
      await refresh();
    } catch {
      setGenerateError("Network error. Please try again.");
    } finally {
      setGenerating(false);
    }
  }, [brand?.id, refresh]);

  const pending = actions.filter((a) => a.approval_state === "pending");
  const completed = actions.filter((a) => a.execution_state === "completed");
  const failed = actions.filter((a) => a.execution_state === "failed" || a.approval_state === "rejected");

  const tabs = [
    { id: "pending", label: "Pending", count: pending.length },
    { id: "completed", label: "Completed", count: completed.length },
    { id: "failed", label: "Failed", count: failed.length },
  ];

  const filtered = activeTab === "pending" ? pending : activeTab === "completed" ? completed : failed;

  if (brandLoading || actionsLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-12 w-96" />
        <div className="space-y-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-32" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight">Actions</h1>
          <p className="text-text-secondary text-sm mt-1">
            Review and approve AI-proposed marketing actions.
          </p>
        </div>
        {brand && audit && (
          <Button
            variant="primary"
            size="md"
            onClick={handleGenerate}
            loading={generating}
          >
            <Sparkles className="w-4 h-4" />
            Generate Actions
          </Button>
        )}
      </div>

      {generateError && (
        <div className="bg-error-dim border border-error/20 text-error text-sm rounded-lg px-4 py-3">
          {generateError}
        </div>
      )}

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {filtered.length === 0 ? (
        <div className="flex flex-col items-center py-16 text-text-tertiary">
          <Zap className="w-10 h-10 mb-3 opacity-30" />
          <p className="text-sm">No {activeTab} actions</p>
          {activeTab === "pending" && audit && actions.length === 0 && (
            <p className="text-xs mt-2">
              Click &quot;Generate Actions&quot; to create proposals from your latest audit.
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((action) => (
            <ActionCard
              key={action.id}
              action={action}
              showActions={activeTab === "pending"}
              onUpdate={refresh}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface ActionCardProps {
  action: Action;
  showActions: boolean;
  onUpdate: () => Promise<void>;
}

function ActionCard({ action, showActions, onUpdate }: ActionCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);
  const supabase = createClient();

  async function handleApprove() {
    setLoading("approved");
    try {
      // Update approval state
      await supabase
        .from("actions")
        .update({
          approval_state: "approved",
          updated_at: new Date().toISOString(),
        })
        .eq("id", action.id);

      // Execute the action
      await fetch("/api/actions/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_id: action.id }),
      });

      await onUpdate();
    } finally {
      setLoading(null);
    }
  }

  async function handleReject() {
    setLoading("rejected");
    try {
      await supabase
        .from("actions")
        .update({
          approval_state: "rejected",
          updated_at: new Date().toISOString(),
        })
        .eq("id", action.id);

      await onUpdate();
    } finally {
      setLoading(null);
    }
  }

  const resultSummary = action.result_summary as Record<string, unknown> | null;

  return (
    <Card>
      <div className="flex items-start gap-4">
        {/* Left: Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <h3 className="text-sm font-semibold">{action.intent || action.action_type}</h3>
            <RiskBadge tier={action.risk_tier} />
            <Badge status={action.approval_state} />
            {action.execution_state !== "pending" && (
              <Badge status={action.execution_state} label={action.execution_state} />
            )}
          </div>

          <div className="flex items-center gap-3 text-xs text-text-tertiary">
            <span className="capitalize">{action.channel}</span>
            <span className="capitalize">{action.action_type.replace(/_/g, " ")}</span>
            <span>{timeAgo(action.created_at)}</span>
            {action.executed_at && (
              <span>Executed {timeAgo(action.executed_at)}</span>
            )}
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {showActions && (
            <>
              <Button
                variant="primary"
                size="sm"
                onClick={handleApprove}
                loading={loading === "approved"}
              >
                <Play className="w-4 h-4" />
                Approve & Run
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={handleReject}
                loading={loading === "rejected"}
              >
                <X className="w-4 h-4" />
                Reject
              </Button>
            </>
          )}
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-2 text-text-tertiary hover:text-foreground transition-colors"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="mt-4 pt-4 border-t border-border space-y-3">
          {Object.keys(action.proposed_changes).length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-text-secondary mb-2">Proposed Changes</h4>
              <pre className="text-xs font-mono bg-bg-elevated rounded-lg p-3 overflow-x-auto text-text-secondary">
                {JSON.stringify(action.proposed_changes, null, 2)}
              </pre>
            </div>
          )}
          {resultSummary && (
            <div>
              <h4 className="text-xs font-medium text-text-secondary mb-2">Result</h4>
              {typeof resultSummary.deliverable === "string" ? (
                <pre className="text-xs font-mono bg-bg-elevated rounded-lg p-3 overflow-x-auto text-text-secondary whitespace-pre-wrap">
                  {resultSummary.deliverable}
                </pre>
              ) : (
                <pre className="text-xs font-mono bg-bg-elevated rounded-lg p-3 overflow-x-auto text-text-secondary">
                  {JSON.stringify(resultSummary, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
