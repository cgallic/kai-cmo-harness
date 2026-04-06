"use client";

import { cn, timeAgo } from "@/lib/utils";
import { Check, X, Loader2, Clock } from "lucide-react";
import type { AgentRun } from "@/lib/types";

interface AIActivityProps {
  runs: AgentRun[];
  loading: boolean;
}

const statusIcons: Record<string, typeof Check> = {
  completed: Check,
  failed: X,
  running: Loader2,
  pending: Clock,
};

export function AIActivity({ runs, loading }: AIActivityProps) {
  if (loading) {
    return (
      <div className="card">
        <h3 className="section-title mb-4">AI Activity (24h)</h3>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 bg-bg-elevated rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  const recent = runs.filter((r) => r.created_at >= cutoff);

  return (
    <div className="card">
      <h3 className="section-title mb-4">AI Activity (24h)</h3>
      {recent.length === 0 ? (
        <p className="text-text-tertiary text-sm py-4 text-center">No agent activity in the last 24 hours</p>
      ) : (
        <div className="space-y-1">
          {recent.map((run) => {
            const StatusIcon = statusIcons[run.status] || Clock;
            const statusColor =
              run.status === "completed" ? "text-success" :
              run.status === "failed" ? "text-error" :
              run.status === "running" ? "text-amber" : "text-text-tertiary";
            const bgColor =
              run.status === "completed" ? "bg-success-dim" :
              run.status === "failed" ? "bg-error-dim" :
              run.status === "running" ? "bg-amber-dim" : "bg-border";

            return (
              <div
                key={run.id}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-bg-elevated transition-colors"
              >
                <div className={cn("w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0", bgColor)}>
                  <StatusIcon className={cn("w-3.5 h-3.5", statusColor)} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate">
                    {run.skill || run.task_type.replace(/_/g, " ")}
                  </p>
                  <p className="text-xs text-text-tertiary">
                    {run.trigger} &middot; {timeAgo(run.created_at)}
                  </p>
                </div>
                {run.status === "failed" && run.error && (
                  <span className="text-xs text-error truncate max-w-[120px]">{run.error}</span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
