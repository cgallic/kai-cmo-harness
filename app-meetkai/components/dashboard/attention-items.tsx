"use client";

import { useMemo } from "react";
import Link from "next/link";
import { AlertTriangle, Clock } from "lucide-react";
import { timeAgo } from "@/lib/utils";
import type { Action, Integration } from "@/lib/types";

interface AttentionItem {
  id: string;
  icon: typeof AlertTriangle;
  iconColor: string;
  title: string;
  subtitle: string;
  href: string;
}

interface AttentionItemsProps {
  actions: Action[];
  integrations: Integration[];
}

export function AttentionItems({ actions, integrations }: AttentionItemsProps) {
  const items = useMemo(() => {
    const result: AttentionItem[] = [];

    const pending = actions.filter((a) => a.approval_state === "pending");
    if (pending.length > 0) {
      result.push({
        id: "pending-actions",
        icon: Clock,
        iconColor: "text-amber",
        title: `${pending.length} action${pending.length > 1 ? "s" : ""} pending approval`,
        subtitle: `Oldest: ${timeAgo(pending[pending.length - 1].created_at)}`,
        href: "/actions",
      });
    }

    const degraded = integrations.filter(
      (i) => i.status === "degraded" || i.status === "error"
    );
    degraded.forEach((i) => {
      result.push({
        id: `degraded-${i.id}`,
        icon: AlertTriangle,
        iconColor: "text-error",
        title: `${i.provider} connection ${i.status}`,
        subtitle: i.last_sync_at ? `Last sync: ${timeAgo(i.last_sync_at)}` : "Never synced",
        href: "/connect",
      });
    });

    const needsProof = integrations.filter(
      (i) => i.status === "connected" && !i.operational
    );
    needsProof.forEach((i) => {
      result.push({
        id: `unverified-${i.id}`,
        icon: AlertTriangle,
        iconColor: "text-amber",
        title: `${i.provider} needs a successful sync`,
        subtitle: "Connected auth is not operational until read or verify passes",
        href: "/connect",
      });
    });

    return result;
  }, [actions, integrations]);

  return (
    <div className="card">
      <h3 className="section-title mb-4">Needs Your Attention</h3>
      {items.length === 0 ? (
        <p className="text-text-tertiary text-sm py-4 text-center">All clear</p>
      ) : (
        <div className="space-y-2">
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.id}
                href={item.href}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-bg-elevated transition-colors"
              >
                <Icon className={`w-4 h-4 ${item.iconColor} flex-shrink-0`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm">{item.title}</p>
                  <p className="text-xs text-text-tertiary">{item.subtitle}</p>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
