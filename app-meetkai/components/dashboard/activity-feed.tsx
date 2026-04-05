"use client";

import { useMemo } from "react";
import { cn, timeAgo, statusColor, scoreColor } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { Action, Audit, Integration } from "@/lib/types";
import { PROVIDERS } from "@/lib/types";
import { Check, X, Clock, AlertTriangle, Loader2, ClipboardCheck, Link2 } from "lucide-react";

interface FeedEvent {
  id: string;
  type: "action" | "audit" | "connection";
  title: string;
  subtitle: string;
  timestamp: string;
  icon: typeof Check;
  iconBg: string;
  iconColor: string;
  badge?: { status: string };
  score?: number;
}

interface ActivityFeedProps {
  actions: Action[];
  audit?: Audit | null;
  integrations?: Integration[];
}

const stateIcons: Record<string, typeof Check> = {
  completed: Check,
  failed: X,
  pending: Clock,
  executing: Loader2,
  rolled_back: AlertTriangle,
};

function actionToEvent(action: Action): FeedEvent {
  const Icon = stateIcons[action.execution_state] || Clock;
  return {
    id: `action-${action.id}`,
    type: "action",
    title: action.intent || action.action_type,
    subtitle: `${action.channel} \u00b7 ${timeAgo(action.updated_at)}`,
    timestamp: action.updated_at,
    icon: Icon,
    iconBg:
      action.execution_state === "completed" ? "bg-success-dim" :
      action.execution_state === "failed" ? "bg-error-dim" :
      action.execution_state === "executing" ? "bg-amber-dim" : "bg-border",
    iconColor: statusColor(action.execution_state),
    badge: { status: action.approval_state },
  };
}

function auditToEvent(audit: Audit): FeedEvent {
  const score = audit.overall_score ?? 0;
  return {
    id: `audit-${audit.id}`,
    type: "audit",
    title: `Audit completed — score: ${Math.round(score)}`,
    subtitle: timeAgo(audit.created_at),
    timestamp: audit.created_at,
    icon: ClipboardCheck,
    iconBg: score >= 70 ? "bg-success-dim" : score >= 40 ? "bg-amber-dim" : "bg-error-dim",
    iconColor: scoreColor(score),
    score,
  };
}

function integrationToEvent(integration: Integration): FeedEvent | null {
  if (integration.status !== "connected" || !integration.connected_at) return null;
  const provider = PROVIDERS.find(
    (p) => p.channel === integration.channel && p.provider === integration.provider
  );
  return {
    id: `conn-${integration.id}`,
    type: "connection",
    title: `${provider?.name || integration.provider} connected`,
    subtitle: timeAgo(integration.connected_at),
    timestamp: integration.connected_at,
    icon: Link2,
    iconBg: "bg-success-dim",
    iconColor: "text-success",
  };
}

export function ActivityFeed({ actions, audit, integrations }: ActivityFeedProps) {
  const events = useMemo(() => {
    const result: FeedEvent[] = [];

    // Action events (non-pending)
    actions
      .filter((a) => a.approval_state !== "pending")
      .forEach((a) => result.push(actionToEvent(a)));

    // Audit event
    if (audit) {
      result.push(auditToEvent(audit));
    }

    // Connection events
    if (integrations) {
      integrations.forEach((i) => {
        const ev = integrationToEvent(i);
        if (ev) result.push(ev);
      });
    }

    // Sort by timestamp descending, take 10
    result.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    return result.slice(0, 10);
  }, [actions, audit, integrations]);

  return (
    <div className="card">
      <h3 className="section-title mb-4">Recent Activity</h3>

      {events.length === 0 ? (
        <p className="text-text-tertiary text-sm py-6 text-center">No activity yet</p>
      ) : (
        <div className="space-y-1">
          {events.map((event) => {
            const Icon = event.icon;
            return (
              <div
                key={event.id}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-bg-elevated transition-colors"
              >
                <div className={cn("w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0", event.iconBg)}>
                  <Icon className={cn("w-3.5 h-3.5", event.iconColor)} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate">{event.title}</p>
                  <p className="text-xs text-text-tertiary">{event.subtitle}</p>
                </div>
                {event.badge && <Badge status={event.badge.status} />}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
