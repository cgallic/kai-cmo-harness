"use client";

import { useState, useEffect } from "react";
import { useBrand, useIntegrations } from "@/lib/hooks";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { createClient } from "@/lib/supabase/client";
import { useRouter, useSearchParams } from "next/navigation";
import { Save, User, Link2, Bell, BarChart3, Search } from "lucide-react";
import type { Integration } from "@/lib/types";

export default function SettingsPage() {
  const { brand, loading } = useBrand();
  const { integrations } = useIntegrations(brand?.id);
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

      <BusinessProfileForm brand={brand} isOnboarding={isOnboarding} />

      {!isOnboarding && (
        <>
          <AnalyticsConfiguration brand={brand} integrations={integrations} />
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
}: {
  brand: ReturnType<typeof useBrand>["brand"];
  isOnboarding: boolean;
}) {
  const router = useRouter();
  const supabase = createClient();
  const [saving, setSaving] = useState(false);
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

interface GA4Property {
  property_id: string;
  display_name: string;
  account_name: string;
}

interface GscSite {
  site_url: string;
  permission_level: string;
}

function AnalyticsConfiguration({
  brand,
  integrations,
}: {
  brand: ReturnType<typeof useBrand>["brand"];
  integrations: Integration[];
}) {
  const supabase = createClient();
  const [ga4Properties, setGa4Properties] = useState<GA4Property[]>([]);
  const [gscSites, setGscSites] = useState<GscSite[]>([]);
  const [loadingGa4, setLoadingGa4] = useState(false);
  const [loadingGsc, setLoadingGsc] = useState(false);
  const [savingGa4, setSavingGa4] = useState(false);
  const [savingGsc, setSavingGsc] = useState(false);

  const ga4Integration = integrations.find(
    (i) => i.provider === "ga4" && i.status === "connected"
  );
  const gscIntegration = integrations.find(
    (i) => i.provider === "google_search_console" && i.status === "connected"
  );

  const selectedGa4Property = (ga4Integration?.config as Record<string, unknown>)
    ?.ga4_property_id as string | undefined;
  const selectedGscSite = (gscIntegration?.config as Record<string, unknown>)
    ?.gsc_site_url as string | undefined;

  useEffect(() => {
    if (ga4Integration && brand) {
      setLoadingGa4(true);
      fetch(`/api/analytics/properties?brand_id=${brand.id}`)
        .then((res) => res.json())
        .then((data: { properties?: GA4Property[] }) => {
          setGa4Properties(data.properties || []);
        })
        .catch(console.error)
        .finally(() => setLoadingGa4(false));
    }
  }, [ga4Integration, brand]);

  useEffect(() => {
    if (gscIntegration && brand) {
      setLoadingGsc(true);
      fetch(`/api/analytics/gsc-sites?brand_id=${brand.id}`)
        .then((res) => res.json())
        .then((data: { sites?: GscSite[] }) => {
          setGscSites(data.sites || []);
        })
        .catch(console.error)
        .finally(() => setLoadingGsc(false));
    }
  }, [gscIntegration, brand]);

  async function handleSelectGa4(propertyId: string) {
    if (!ga4Integration) return;
    setSavingGa4(true);
    const newConfig = { ...(ga4Integration.config || {}), ga4_property_id: propertyId };
    await supabase
      .from("integrations")
      .update({ config: newConfig, updated_at: new Date().toISOString() })
      .eq("id", ga4Integration.id);
    setSavingGa4(false);
    window.location.reload();
  }

  async function handleSelectGsc(siteUrl: string) {
    if (!gscIntegration) return;
    setSavingGsc(true);
    const newConfig = { ...(gscIntegration.config || {}), gsc_site_url: siteUrl };
    await supabase
      .from("integrations")
      .update({ config: newConfig, updated_at: new Date().toISOString() })
      .eq("id", gscIntegration.id);
    setSavingGsc(false);
    window.location.reload();
  }

  if (!ga4Integration && !gscIntegration) return null;

  const selectedGa4Name = ga4Properties.find(
    (p) => p.property_id === selectedGa4Property
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-amber" />
          Analytics Configuration
        </CardTitle>
      </CardHeader>

      <div className="space-y-4">
        {/* GA4 Property Selector */}
        {ga4Integration && (
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1.5">
              Google Analytics Property
            </label>
            {loadingGa4 ? (
              <Skeleton className="h-10 w-full" />
            ) : ga4Properties.length === 0 ? (
              <p className="text-xs text-text-tertiary">
                No GA4 properties found for this account.
              </p>
            ) : (
              <>
                <select
                  value={selectedGa4Property || ""}
                  onChange={(e) => handleSelectGa4(e.target.value)}
                  disabled={savingGa4}
                  className="w-full px-4 py-2.5 bg-background border border-border rounded-[12px] text-foreground focus:outline-none focus:border-amber transition-colors disabled:opacity-50"
                >
                  <option value="">Select a property...</option>
                  {ga4Properties.map((prop) => (
                    <option key={prop.property_id} value={prop.property_id}>
                      {prop.display_name} ({prop.account_name})
                    </option>
                  ))}
                </select>
                {selectedGa4Name && (
                  <p className="text-xs text-text-tertiary mt-1">
                    Currently using: {selectedGa4Name.display_name}
                  </p>
                )}
              </>
            )}
          </div>
        )}

        {/* GSC Site Selector */}
        {gscIntegration && (
          <div>
            <label className="flex items-center gap-1.5 text-sm font-medium text-text-secondary mb-1.5">
              <Search className="w-3.5 h-3.5" />
              Search Console Site
            </label>
            {loadingGsc ? (
              <Skeleton className="h-10 w-full" />
            ) : gscSites.length === 0 ? (
              <p className="text-xs text-text-tertiary">
                No Search Console sites found for this account.
              </p>
            ) : (
              <>
                <select
                  value={selectedGscSite || ""}
                  onChange={(e) => handleSelectGsc(e.target.value)}
                  disabled={savingGsc}
                  className="w-full px-4 py-2.5 bg-background border border-border rounded-[12px] text-foreground focus:outline-none focus:border-amber transition-colors disabled:opacity-50"
                >
                  <option value="">Select a site...</option>
                  {gscSites.map((site) => (
                    <option key={site.site_url} value={site.site_url}>
                      {site.site_url} ({site.permission_level})
                    </option>
                  ))}
                </select>
                {selectedGscSite && (
                  <p className="text-xs text-text-tertiary mt-1">
                    Currently using: {selectedGscSite}
                  </p>
                )}
              </>
            )}
          </div>
        )}
      </div>
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
