"use client";

import { useRouter } from "next/navigation";
import { cn, formatNumber, timeAgo } from "@/lib/utils";
import type { ChannelSnapshot, Integration, Action, Audit } from "@/lib/types";

interface StatItem {
  label: string;
  value: string | number;
  color: string;
  subtitle: string | null;
  href: string;
}

interface QuickStatsProps {
  audit: Audit | null;
  integrations: Integration[];
  actions: Action[];
  snapshots: ChannelSnapshot[];
}

export function QuickStats({ audit, integrations, actions, snapshots }: QuickStatsProps) {
  const router = useRouter();
  const connected = integrations.filter((i) => i.status === "connected").length;
  const pending = actions.filter((a) => a.approval_state === "pending").length;

  // Extract sessions from latest GA4 snapshot
  const gaSnapshot = snapshots.find((s) => s.channel === "analytics" && s.provider === "ga4");
  const sessions = (gaSnapshot?.snapshot_data as Record<string, number>)?.sessions ?? null;

  // Determine last sync time from integrations or snapshot
  const latestSyncAt = integrations
    .filter((i) => i.last_sync_at)
    .map((i) => i.last_sync_at as string)
    .sort()
    .pop();
  const sessionsSyncLabel = gaSnapshot
    ? `Synced ${timeAgo(gaSnapshot.created_at)}`
    : latestSyncAt
      ? `Synced ${timeAgo(latestSyncAt)}`
      : null;

  const stats: StatItem[] = [
    {
      label: "Audit Score",
      value: audit?.overall_score ? Math.round(audit.overall_score) : "—",
      color: audit?.overall_score
        ? audit.overall_score >= 70 ? "text-success" : audit.overall_score >= 40 ? "text-amber" : "text-error"
        : "text-text-tertiary",
      subtitle: audit?.created_at ? `Audited ${timeAgo(audit.created_at)}` : null,
      href: "/analytics",
    },
    {
      label: "Connected",
      value: connected,
      color: connected > 0 ? "text-success" : "text-text-tertiary",
      subtitle: null,
      href: "/connect",
    },
    {
      label: "Pending Actions",
      value: pending,
      color: pending > 0 ? "text-amber" : "text-text-tertiary",
      subtitle: null,
      href: "/actions",
    },
    {
      label: "Sessions (28d)",
      value: sessions !== null ? formatNumber(sessions) : "—",
      color: "text-foreground",
      subtitle: sessionsSyncLabel,
      href: "/analytics",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => (
        <button
          key={stat.label}
          onClick={() => router.push(stat.href)}
          className="card text-left cursor-pointer hover:border-border-hover transition-colors"
        >
          <p className="text-text-secondary text-xs font-medium mb-1">{stat.label}</p>
          <p className={cn("stat-number", stat.color)}>{stat.value}</p>
          {stat.subtitle && (
            <p className="text-text-tertiary text-[10px] mt-1">{stat.subtitle}</p>
          )}
        </button>
      ))}
    </div>
  );
}
