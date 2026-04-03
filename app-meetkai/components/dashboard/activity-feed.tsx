"use client";

import { cn, timeAgo, statusColor } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { Action } from "@/lib/types";
import { Check, X, Clock, AlertTriangle, Loader2 } from "lucide-react";

interface ActivityFeedProps {
  actions: Action[];
}

const stateIcons: Record<string, typeof Check> = {
  completed: Check,
  failed: X,
  pending: Clock,
  executing: Loader2,
  rolled_back: AlertTriangle,
};

export function ActivityFeed({ actions }: ActivityFeedProps) {
  const recent = actions
    .filter((a) => a.approval_state !== "pending")
    .slice(0, 10);

  return (
    <div className="card">
      <h3 className="section-title mb-4">Recent Activity</h3>

      {recent.length === 0 ? (
        <p className="text-text-tertiary text-sm py-6 text-center">No activity yet</p>
      ) : (
        <div className="space-y-1">
          {recent.map((action) => {
            const Icon = stateIcons[action.execution_state] || Clock;
            return (
              <div
                key={action.id}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-bg-elevated transition-colors"
              >
                <div className={cn("w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0",
                  action.execution_state === "completed" ? "bg-success-dim" :
                  action.execution_state === "failed" ? "bg-error-dim" :
                  action.execution_state === "executing" ? "bg-amber-dim" : "bg-border"
                )}>
                  <Icon className={cn("w-3.5 h-3.5",
                    statusColor(action.execution_state),
                    action.execution_state === "executing" && "animate-spin"
                  )} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate">
                    {action.intent || action.action_type}
                  </p>
                  <p className="text-xs text-text-tertiary">
                    {action.channel} &middot; {timeAgo(action.updated_at)}
                  </p>
                </div>
                <Badge status={action.approval_state} />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
