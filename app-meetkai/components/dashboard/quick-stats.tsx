"use client";

import { cn, formatNumber } from "@/lib/utils";
import type { ChannelSnapshot, Integration, Action, Audit } from "@/lib/types";

interface QuickStatsProps {
  audit: Audit | null;
  integrations: Integration[];
  actions: Action[];
  snapshots: ChannelSnapshot[];
}

export function QuickStats({ audit, integrations, actions, snapshots }: QuickStatsProps) {
  const connected = integrations.filter((i) => i.status === "connected").length;
  const pending = actions.filter((a) => a.approval_state === "pending").length;

  // Extract sessions from latest GA4 snapshot
  const gaSnapshot = snapshots.find((s) => s.channel === "analytics" && s.provider === "ga4");
  const sessions = (gaSnapshot?.snapshot_data as Record<string, number>)?.sessions ?? null;

  const stats = [
    {
      label: "Audit Score",
      value: audit?.overall_score ? Math.round(audit.overall_score) : "—",
      color: audit?.overall_score
        ? audit.overall_score >= 70 ? "text-success" : audit.overall_score >= 40 ? "text-amber" : "text-error"
        : "text-text-tertiary",
    },
    {
      label: "Connected",
      value: connected,
      color: connected > 0 ? "text-success" : "text-text-tertiary",
    },
    {
      label: "Pending Actions",
      value: pending,
      color: pending > 0 ? "text-amber" : "text-text-tertiary",
    },
    {
      label: "Sessions (28d)",
      value: sessions !== null ? formatNumber(sessions) : "—",
      color: "text-foreground",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => (
        <div key={stat.label} className="card">
          <p className="text-text-secondary text-xs font-medium mb-1">{stat.label}</p>
          <p className={cn("stat-number", stat.color)}>{stat.value}</p>
        </div>
      ))}
    </div>
  );
}
