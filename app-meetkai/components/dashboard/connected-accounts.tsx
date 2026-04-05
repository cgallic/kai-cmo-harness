"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { PROVIDERS, type Integration } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Plus } from "lucide-react";

interface ConnectedAccountsProps {
  integrations: Integration[];
}

/**
 * Determine the health of an integration based on status and last sync freshness.
 * Green: connected AND last synced within 24h
 * Yellow: connected but last sync > 24h ago (or never synced)
 * Red: status is "error" or "degraded"
 */
function healthColor(integration: Integration): string {
  if (integration.status === "error" || integration.status === "degraded") {
    return "bg-error";
  }
  if (integration.status === "connected") {
    const syncRef = integration.last_sync_at || integration.updated_at;
    if (syncRef) {
      const hoursSinceSync = (Date.now() - new Date(syncRef).getTime()) / (1000 * 60 * 60);
      if (hoursSinceSync <= 24) return "bg-success";
    }
    return "bg-amber";
  }
  return "bg-text-tertiary";
}

function healthTitle(integration: Integration): string {
  if (integration.status === "error") return "Error";
  if (integration.status === "degraded") return "Degraded";
  if (integration.status === "connected") {
    const syncRef = integration.last_sync_at || integration.updated_at;
    if (syncRef) {
      const hoursSinceSync = (Date.now() - new Date(syncRef).getTime()) / (1000 * 60 * 60);
      if (hoursSinceSync <= 24) return "Healthy — synced recently";
      return `Stale — last synced ${Math.round(hoursSinceSync)}h ago`;
    }
    return "Connected — never synced";
  }
  return integration.status;
}

export function ConnectedAccounts({ integrations }: ConnectedAccountsProps) {
  const connected = integrations.filter((i) => i.status === "connected");
  const total = PROVIDERS.length;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="section-title">Connected Accounts</h3>
        <span className="text-text-tertiary text-sm font-mono">
          {connected.length}/{total}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {integrations.map((integration) => {
          const provider = PROVIDERS.find(
            (p) => p.channel === integration.channel && p.provider === integration.provider
          );
          return (
            <div
              key={integration.id}
              className="flex items-center gap-2.5 px-3 py-2.5 bg-bg-elevated rounded-lg border border-border"
            >
              <span
                className={cn("w-2 h-2 rounded-full flex-shrink-0", healthColor(integration))}
                title={healthTitle(integration)}
              />
              <span className="text-sm">{provider?.name || integration.provider}</span>
              <Badge status={integration.status} className="ml-auto text-[10px]" />
            </div>
          );
        })}

        <Link
          href="/connect"
          className="flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg border border-dashed border-border-hover text-text-tertiary hover:text-amber hover:border-amber transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span className="text-sm">Connect</span>
        </Link>
      </div>
    </div>
  );
}
