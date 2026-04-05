"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge, RiskBadge } from "@/components/ui/badge";
import { createClient } from "@/lib/supabase/client";
import { timeAgo } from "@/lib/utils";
import type { Action } from "@/lib/types";
import { Zap, Check, X } from "lucide-react";
import Link from "next/link";

interface PendingActionsProps {
  actions: Action[];
}

export function PendingActions({ actions }: PendingActionsProps) {
  const pending = actions.filter((a) => a.approval_state === "pending").slice(0, 5);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="section-title">Pending Actions</h3>
        {actions.length > 0 && (
          <Link href="/actions" className="text-amber text-sm hover:underline">
            View all
          </Link>
        )}
      </div>

      {pending.length === 0 ? (
        <div className="flex flex-col items-center py-8 text-text-tertiary">
          <Zap className="w-8 h-8 mb-2 opacity-40" />
          <p className="text-sm">No pending actions</p>
        </div>
      ) : (
        <div className="space-y-3">
          {pending.map((action) => (
            <PendingActionCard key={action.id} action={action} />
          ))}
        </div>
      )}
    </div>
  );
}

function PendingActionCard({ action }: { action: Action }) {
  const [loading, setLoading] = useState<"approve" | "reject" | null>(null);
  const supabase = createClient();

  async function handleApprove() {
    setLoading("approve");
    try {
      // Approve the action
      await supabase
        .from("actions")
        .update({
          approval_state: "approved",
          updated_at: new Date().toISOString(),
        })
        .eq("id", action.id);

      // Execute it
      await fetch("/api/actions/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_id: action.id }),
      });
    } finally {
      setLoading(null);
    }
  }

  async function handleReject() {
    setLoading("reject");
    try {
      await supabase
        .from("actions")
        .update({
          approval_state: "rejected",
          updated_at: new Date().toISOString(),
        })
        .eq("id", action.id);
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="flex items-start gap-3 p-3 bg-bg-elevated rounded-lg border border-border">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-medium truncate">{action.intent || action.action_type}</span>
          <RiskBadge tier={action.risk_tier} />
        </div>
        <div className="flex items-center gap-2 text-xs text-text-tertiary">
          <span className="capitalize">{action.channel}</span>
          <span>&middot;</span>
          <span>{timeAgo(action.created_at)}</span>
        </div>
      </div>
      <div className="flex items-center gap-1.5">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleApprove}
          loading={loading === "approve"}
          className="text-success hover:bg-success-dim"
        >
          <Check className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleReject}
          loading={loading === "reject"}
          className="text-error hover:bg-error-dim"
        >
          <X className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
