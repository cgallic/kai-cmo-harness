"use client";

import { useState } from "react";
import { useBrand, useActions } from "@/lib/hooks";
import { Tabs } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge, RiskBadge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { createClient } from "@/lib/supabase/client";
import { cn, timeAgo } from "@/lib/utils";
import type { Action } from "@/lib/types";
import { Check, X, Clock, ChevronDown, ChevronUp, Zap } from "lucide-react";

export default function ActionsPage() {
  const { brand, loading: brandLoading } = useBrand();
  const { actions, loading: actionsLoading } = useActions(brand?.id);
  const [activeTab, setActiveTab] = useState("pending");

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
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight">Actions</h1>
        <p className="text-text-secondary text-sm mt-1">
          Review and approve AI-proposed marketing actions.
        </p>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {filtered.length === 0 ? (
        <div className="flex flex-col items-center py-16 text-text-tertiary">
          <Zap className="w-10 h-10 mb-3 opacity-30" />
          <p className="text-sm">No {activeTab} actions</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((action) => (
            <ActionCard key={action.id} action={action} showActions={activeTab === "pending"} />
          ))}
        </div>
      )}
    </div>
  );
}

function ActionCard({ action, showActions }: { action: Action; showActions: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);
  const supabase = createClient();

  async function handleAction(state: "approved" | "rejected") {
    setLoading(state);
    await supabase
      .from("actions")
      .update({
        approval_state: state,
        updated_at: new Date().toISOString(),
      })
      .eq("id", action.id);
    setLoading(null);
  }

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
                onClick={() => handleAction("approved")}
                loading={loading === "approved"}
              >
                <Check className="w-4 h-4" />
                Approve
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={() => handleAction("rejected")}
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
          {action.result_summary && (
            <div>
              <h4 className="text-xs font-medium text-text-secondary mb-2">Result</h4>
              <pre className="text-xs font-mono bg-bg-elevated rounded-lg p-3 overflow-x-auto text-text-secondary">
                {JSON.stringify(action.result_summary, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
