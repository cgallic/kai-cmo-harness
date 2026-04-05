"use client";

import { useState, useEffect, useCallback } from "react";
import { useBrand, useIntegrations, useAudit } from "@/lib/hooks";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { createClient } from "@/lib/supabase/client";
import { useRouter, useSearchParams } from "next/navigation";
import { Save, User, Link2, Bell, Search } from "lucide-react";
import { cn, scoreColor, timeAgo } from "@/lib/utils";
import type { Audit } from "@/lib/types";

export default function SettingsPage() {
  const { brand, loading } = useBrand();
  const { integrations } = useIntegrations(brand?.id);
  const { audit, setAudit } = useAudit(brand?.id);
  const searchParams = useSearchParams();
  const isOnboarding = searchParams.get("onboarding") === "true";

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight">
          {isOnboarding ? "Set Up Your Business" : "Settings"}
        </h1>
        {isOnboarding && (
          <p className="text-text-secondary text-sm mt-1">
            Tell us about your business to get personalized marketing recommendations.
          </p>
        )}
      </div>

      <BusinessProfileForm brand={brand} isOnboarding={isOnboarding} audit={audit} brandId={brand?.id} onAuditComplete={setAudit} />

      {!isOnboarding && (
        <>
          <ConnectedAccountsList integrations={integrations} />
          <NotificationPreferences brand={brand} />
        </>
      )}
    </div>
  );
}

function BusinessProfileForm({
  brand,
  isOnboarding,
  audit,
  brandId,
  onAuditComplete,
}: {
  brand: ReturnType<typeof useBrand>["brand"];
  isOnboarding: boolean;
  audit: Audit | null;
  brandId: string | undefined;
  onAuditComplete: (audit: Audit) => void;
}) {
  const router = useRouter();
  const supabase = createClient();
  const [saving, setSaving] = useState(false);
  const [auditRunning, setAuditRunning] = useState(false);
  const [auditError, setAuditError] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: brand?.name || "",
    url: brand?.url || "",
    description: brand?.description || "",
    archetype: brand?.archetype || "local_service",
  });

  useEffect(() => {
    if (brand) {
      setForm({
        name: brand.name,
        url: brand.url || "",
        description: brand.description || "",
        archetype: brand.archetype,
      });
    }
  }, [brand]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);

    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    if (brand) {
      await supabase.from("brands").update({
        ...form,
        updated_at: new Date().toISOString(),
      }).eq("id", brand.id);
    } else {
      await supabase.from("brands").insert({
        ...form,
        user_id: user.id,
      });
    }

    setSaving(false);
    if (isOnboarding) {
      router.push("/dashboard");
    }
  }

  const runAudit = useCallback(async () => {
    if (!brandId || auditRunning) return;
    setAuditRunning(true);
    setAuditError(null);

    try {
      const res = await fetch("/api/audits/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brand_id: brandId, domain: brand?.url }),
      });

      const data = await res.json();

      if (!res.ok) {
        setAuditError(data.error || "Audit failed");
        return;
      }

      const newAudit: Audit = {
        id: data.audit_id,
        brand_id: brandId,
        overall_score: data.overall_score,
        category_scores: data.category_scores || {},
        findings: data.findings || [],
        metadata: {},
        created_at: data.created_at || new Date().toISOString(),
      };
      onAuditComplete(newAudit);
    } catch {
      setAuditError("Network error. Please try again.");
    } finally {
      setAuditRunning(false);
    }
  }, [brandId, brand?.url, auditRunning, onAuditComplete]);

  const archetypes = [
    { value: "local_service", label: "Local Service Business" },
    { value: "ecommerce", label: "E-Commerce" },
    { value: "saas", label: "SaaS / Software" },
    { value: "agency", label: "Agency / Consultancy" },
    { value: "content", label: "Content / Media" },
    { value: "other", label: "Other" },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <User className="w-4 h-4 text-amber" />
          Business Profile
        </CardTitle>
      </CardHeader>

      <form onSubmit={handleSave} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1.5">Business Name</label>
          <input
            type="text"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
            placeholder="Acme Marketing Co."
            className="w-full px-4 py-2.5 bg-background border border-border rounded-[12px] text-foreground placeholder:text-text-tertiary focus:outline-none focus:border-amber transition-colors"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1.5">Website URL</label>
          <input
            type="url"
            value={form.url}
            onChange={(e) => setForm({ ...form, url: e.target.value })}
            placeholder="https://example.com"
            className="w-full px-4 py-2.5 bg-background border border-border rounded-[12px] text-foreground placeholder:text-text-tertiary focus:outline-none focus:border-amber transition-colors"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1.5">Business Type</label>
          <select
            value={form.archetype}
            onChange={(e) => setForm({ ...form, archetype: e.target.value })}
            className="w-full px-4 py-2.5 bg-background border border-border rounded-[12px] text-foreground focus:outline-none focus:border-amber transition-colors"
          >
            {archetypes.map((a) => (
              <option key={a.value} value={a.value}>{a.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1.5">Description</label>
          <textarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Brief description of your business..."
            rows={3}
            className="w-full px-4 py-2.5 bg-background border border-border rounded-[12px] text-foreground placeholder:text-text-tertiary focus:outline-none focus:border-amber transition-colors resize-none"
          />
        </div>

        <Button type="submit" loading={saving} className="w-full">
          <Save className="w-4 h-4" />
          {isOnboarding ? "Create Profile & Continue" : "Save Changes"}
        </Button>
      </form>

      {/* Audit section — shown after profile exists */}
      {!isOnboarding && brand && (
        <div className="mt-6 pt-6 border-t border-border">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-foreground">Marketing Audit</h4>
            {audit && (
              <div className="flex items-center gap-2 text-xs text-text-tertiary">
                <span>Last run: {timeAgo(audit.created_at)}</span>
                <span className={cn("font-mono font-semibold", scoreColor(audit.overall_score ?? 0))}>
                  {audit.overall_score ?? "—"}/100
                </span>
              </div>
            )}
          </div>

          {auditError && (
            <div className="bg-error-dim border border-error/20 rounded-lg px-3 py-2 text-xs text-error mb-3">
              {auditError}
            </div>
          )}

          <Button
            variant="secondary"
            size="sm"
            loading={auditRunning}
            disabled={!brand.url}
            onClick={runAudit}
            className="w-full"
          >
            <Search className="w-3.5 h-3.5" />
            {audit ? "Run New Audit" : "Run First Audit"}
          </Button>

          {!brand.url && (
            <p className="text-xs text-text-tertiary mt-2">
              Save a website URL above to enable audits.
            </p>
          )}
        </div>
      )}
    </Card>
  );
}

function ConnectedAccountsList({ integrations }: { integrations: ReturnType<typeof useIntegrations>["integrations"] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Link2 className="w-4 h-4 text-amber" />
          Connected Accounts
        </CardTitle>
      </CardHeader>

      {integrations.length === 0 ? (
        <div className="text-center py-6">
          <p className="text-text-tertiary text-sm mb-2">No accounts connected yet.</p>
          <a href="/connect" className="text-amber text-sm hover:underline">Connect your first account</a>
        </div>
      ) : (
        <div className="space-y-2">
          {integrations.map((integration) => (
            <div
              key={integration.id}
              className="flex items-center justify-between px-3 py-2.5 bg-bg-elevated rounded-lg"
            >
              <div>
                <span className="text-sm font-medium capitalize">{integration.provider.replace(/_/g, " ")}</span>
                <span className="text-xs text-text-tertiary ml-2 capitalize">{integration.channel}</span>
              </div>
              <Badge status={integration.status} />
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function NotificationPreferences({ brand }: { brand: ReturnType<typeof useBrand>["brand"] }) {
  const supabase = createClient();
  const prefs = (brand?.metadata as Record<string, Record<string, boolean>>)?.notifications || {};

  const [settings, setSettings] = useState({
    action_completed: prefs.action_completed ?? true,
    connection_degraded: prefs.connection_degraded ?? true,
    weekly_summary: prefs.weekly_summary ?? true,
  });

  async function toggleSetting(key: keyof typeof settings) {
    const newSettings = { ...settings, [key]: !settings[key] };
    setSettings(newSettings);

    if (brand) {
      await supabase.from("brands").update({
        metadata: { ...(brand.metadata as object), notifications: newSettings },
        updated_at: new Date().toISOString(),
      }).eq("id", brand.id);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bell className="w-4 h-4 text-amber" />
          Notifications
        </CardTitle>
      </CardHeader>

      <div className="space-y-3">
        {[
          { key: "action_completed" as const, label: "Action completed", desc: "Get notified when an approved action finishes executing" },
          { key: "connection_degraded" as const, label: "Connection issues", desc: "Alert when a connected account loses access" },
          { key: "weekly_summary" as const, label: "Weekly summary", desc: "Receive a weekly marketing performance digest" },
        ].map((item) => (
          <div key={item.key} className="flex items-center justify-between px-3 py-2.5 bg-bg-elevated rounded-lg">
            <div>
              <p className="text-sm font-medium">{item.label}</p>
              <p className="text-xs text-text-tertiary">{item.desc}</p>
            </div>
            <button
              onClick={() => toggleSetting(item.key)}
              className={`relative w-10 h-6 rounded-full transition-colors ${settings[item.key] ? "bg-amber" : "bg-border"}`}
            >
              <span
                className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${settings[item.key] ? "left-5" : "left-1"}`}
              />
            </button>
          </div>
        ))}
      </div>
    </Card>
  );
}
