"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { PROVIDERS, type Integration } from "@/lib/types";
import { Plus } from "lucide-react";

interface ConnectedAccountsProps {
  integrations: Integration[];
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
