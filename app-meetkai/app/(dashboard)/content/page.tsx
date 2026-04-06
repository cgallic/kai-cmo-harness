"use client";

import { useState, useCallback } from "react";
import { useBrand, useActions, useContent } from "@/lib/hooks";
import { Tabs } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge, RiskBadge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { createClient } from "@/lib/supabase/client";
import { cn, timeAgo } from "@/lib/utils";
import type { Action, Content } from "@/lib/types";
import { Check, X, ChevronDown, ChevronUp, FileText, Play, Eye } from "lucide-react";

export default function ContentPage() {
  const { brand, loading: brandLoading } = useBrand();
  const { actions, loading: actionsLoading, refresh: refreshActions } = useActions(brand?.id);
  const { content, loading: contentLoading, refresh: refreshContent } = useContent(brand?.id);
  const [activeTab, setActiveTab] = useState("pending");

  const pending = actions.filter((a) => a.approval_state === "pending");
  const inProgress = actions.filter((a) => a.execution_state === "executing");
  const completed = actions.filter((a) => a.execution_state === "completed");

  const tabs = [
    { id: "pending", label: "Pending", count: pending.length },
    { id: "in-progress", label: "In Progress", count: inProgress.length },
    { id: "completed", label: "Completed", count: completed.length },
    { id: "library", label: "Content Library", count: content.length },
  ];

  const filtered =
    activeTab === "pending" ? pending :
    activeTab === "in-progress" ? inProgress :
    activeTab === "completed" ? completed : [];

  if (brandLoading || actionsLoading || contentLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-12 w-full" />
        <div className="space-y-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-32" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight">Content & Actions</h1>
        <p className="text-text-secondary text-sm mt-1">
          AI-generated content and marketing actions.
        </p>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === "library" ? (
        <ContentLibrary content={content} />
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center py-16 text-text-tertiary">
          <FileText className="w-10 h-10 mb-3 opacity-30" />
          <p className="text-sm">No {activeTab.replace("-", " ")} items</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((action) => (
            <ActionCard
              key={action.id}
              action={action}
              showActions={activeTab === "pending"}
              onUpdate={() => { refreshActions(); refreshContent(); }}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function ContentLibrary({ content }: { content: Content[] }) {
  if (content.length === 0) {
    return (
      <div className="flex flex-col items-center py-16 text-text-tertiary">
        <FileText className="w-10 h-10 mb-3 opacity-30" />
        <p className="text-sm">No content generated yet</p>
        <p className="text-xs mt-1">Content will appear here after actions are executed.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {content.map((item) => (
        <ContentCard key={item.id} item={item} />
      ))}
    </div>
  );
}

function ContentCard({ item }: { item: Content }) {
  const [expanded, setExpanded] = useState(false);
  const gateReport = item.gate_report as Record<string, unknown> | null;
  const fourUsScore = gateReport?.four_us_total as number | undefined;

  return (
    <Card>
      <div className="flex items-start gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <h3 className="text-sm font-semibold">{item.title || "Untitled"}</h3>
            <Badge status={item.status} />
            <span className="text-xs text-text-tertiary capitalize">{item.format}</span>
            {item.skill && (
              <span className="text-xs text-text-tertiary">{item.skill}</span>
            )}
          </div>
          <div className="flex items-center gap-3 text-xs text-text-tertiary">
            <span>{timeAgo(item.created_at)}</span>
            {fourUsScore != null && (
              <span className={cn(
                "font-mono font-semibold",
                fourUsScore >= 12 ? "text-success" : fourUsScore >= 10 ? "text-amber" : "text-error"
              )}>
                4U: {fourUsScore}/16
              </span>
            )}
          </div>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="p-2 text-text-tertiary hover:text-foreground transition-colors"
        >
          {expanded ? <ChevronUp className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
        </button>
      </div>
      {expanded && item.body && (
        <div className="mt-4 pt-4 border-t border-border">
          <pre className="text-xs font-mono bg-bg-elevated rounded-lg p-3 overflow-x-auto text-text-secondary whitespace-pre-wrap max-h-96 overflow-y-auto">
            {item.body}
          </pre>
        </div>
      )}
    </Card>
  );
}

function ActionCard({
  action,
  showActions,
  onUpdate,
}: {
  action: Action;
  showActions: boolean;
  onUpdate: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);
  const supabase = createClient();

  async function handleApprove() {
    setLoading("approved");
    try {
      await supabase
        .from("actions")
        .update({ approval_state: "approved" })
        .eq("id", action.id);
      await fetch("/api/actions/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_id: action.id }),
      });
      onUpdate();
    } finally {
      setLoading(null);
    }
  }

  async function handleReject() {
    setLoading("rejected");
    try {
      await supabase
        .from("actions")
        .update({ approval_state: "rejected" })
        .eq("id", action.id);
      onUpdate();
    } finally {
      setLoading(null);
    }
  }

  const resultSummary = action.result_summary as Record<string, unknown> | null;

  return (
    <Card>
      <div className="flex items-start gap-4">
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
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {showActions && (
            <>
              <Button variant="primary" size="sm" onClick={handleApprove} loading={loading === "approved"}>
                <Play className="w-4 h-4" />
                Approve
              </Button>
              <Button variant="danger" size="sm" onClick={handleReject} loading={loading === "rejected"}>
                <X className="w-4 h-4" />
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
