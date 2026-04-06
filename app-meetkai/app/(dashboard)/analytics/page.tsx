"use client";

import { useState } from "react";
import { useBrand, useSnapshots, useIntegrations } from "@/lib/hooks";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn, formatNumber, formatPercent } from "@/lib/utils";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import {
  BarChart3, TrendingUp, Users, Eye, RefreshCw, Search,
  Facebook, Instagram, Linkedin, Youtube, Pin,
  Megaphone, Target, Mail, Send, Zap, UserCheck, CreditCard,
  ChevronDown, Twitter, Calendar, BookOpen, Table2,
  MessageSquare, Layout, SquareCode, MapPin, Globe, ShoppingBag,
} from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import type { ChannelSnapshot } from "@/lib/types";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface GA4Property {
  property_id: string;
  display_name: string;
  account_name: string;
}

interface SyncResponse {
  status?: string;
  error?: string;
  properties?: GA4Property[];
  data?: Record<string, unknown>;
}

interface GscSyncResponse {
  status?: string;
  error?: string;
  sites?: { site_url: string; permission_level: string }[];
  data?: Record<string, unknown>;
}

/* ------------------------------------------------------------------ */
/*  Sync endpoint map (mirrors connect page)                           */
/* ------------------------------------------------------------------ */

const SYNC_ENDPOINTS: Record<string, string> = {
  ga4: "/api/analytics/sync",
  gsc: "/api/analytics/sync-gsc",
  facebook: "/api/sync/facebook",
  instagram: "/api/sync/instagram",
  linkedin: "/api/sync/linkedin",
  youtube: "/api/sync/youtube",
  pinterest: "/api/sync/pinterest",
  google_ads: "/api/sync/google-ads",
  meta_ads: "/api/sync/meta-ads",
  mailchimp: "/api/sync/mailchimp",
  sendgrid: "/api/sync/sendgrid",
  klaviyo: "/api/sync/klaviyo",
  hubspot: "/api/sync/hubspot",
  stripe: "/api/sync/stripe",
  convertkit: "/api/sync/convertkit",
  activecampaign: "/api/sync/activecampaign",
  twitter: "/api/sync/twitter",
  calendly: "/api/sync/calendly",
  notion: "/api/sync/notion",
  google_sheets: "/api/sync/google-sheets",
  airtable: "/api/sync/airtable",
  wordpress: "/api/sync/wordpress",
  shopify: "/api/sync/shopify",
  webflow: "/api/sync/webflow",
  squarespace: "/api/sync/squarespace",
  slack: "/api/sync/slack",
  gbp: "/api/sync/gbp",
};

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function formatDollar(n: number) {
  return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function getSnap(snapshots: ChannelSnapshot[], provider: string) {
  const s = snapshots.find((s) => s.provider === provider);
  return s ? (s.snapshot_data as Record<string, unknown>) : null;
}

/* ------------------------------------------------------------------ */
/*  ProviderMetricCard                                                 */
/* ------------------------------------------------------------------ */

function MetricCard({
  icon: Icon,
  name,
  metrics,
  color,
}: {
  icon: typeof BarChart3;
  name: string;
  metrics: { label: string; value: string }[];
  color: string;
}) {
  return (
    <Card>
      <div className="flex items-center gap-2 mb-3">
        <Icon className={cn("w-4 h-4", color)} />
        <span className="text-sm font-semibold">{name}</span>
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-2">
        {metrics.map((m) => (
          <div key={m.label}>
            <p className="text-[10px] text-text-tertiary uppercase tracking-wide">{m.label}</p>
            <p className="text-sm font-mono font-medium">{m.value}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

/* ------------------------------------------------------------------ */
/*  Section wrapper                                                    */
/* ------------------------------------------------------------------ */

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(true);
  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 mb-3 group"
      >
        <ChevronDown className={cn("w-4 h-4 text-text-tertiary transition-transform", !open && "-rotate-90")} />
        <h2 className="font-display text-lg font-semibold group-hover:text-amber transition-colors">{title}</h2>
      </button>
      {open && children}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main page                                                          */
/* ------------------------------------------------------------------ */

export default function AnalyticsPage() {
  const { brand, loading: brandLoading } = useBrand();
  // Fetch ALL snapshots (no channel filter) so we see every provider
  const { snapshots, loading: snapshotLoading, refresh: refreshSnapshots } = useSnapshots(brand?.id);
  const { integrations } = useIntegrations(brand?.id);
  const [range, setRange] = useState("28d");
  const [syncing, setSyncing] = useState(false);
  const [syncingGsc, setSyncingGsc] = useState(false);
  const [syncingAll, setSyncingAll] = useState(false);
  const [needsPropertySelection, setNeedsPropertySelection] = useState(false);
  const [availableProperties, setAvailableProperties] = useState<GA4Property[]>([]);
  const [selectingProperty, setSelectingProperty] = useState(false);

  const ga4Connected = integrations.some((i) => i.provider === "ga4" && i.status === "connected");
  const gscConnected = integrations.some((i) => i.provider === "gsc" && i.status === "connected");
  const connectedProviders = integrations.filter((i) => i.status === "connected").map((i) => i.provider);

  async function handleSelectProperty(propertyId: string) {
    if (!brand) return;
    setSelectingProperty(true);
    const supabase = createClient();
    const ga4Integration = integrations.find((i) => i.provider === "ga4" && i.status === "connected");
    if (ga4Integration) {
      const newConfig = { ...(ga4Integration.config || {}), ga4_property_id: propertyId };
      await supabase
        .from("integrations")
        .update({ config: newConfig, updated_at: new Date().toISOString() })
        .eq("id", ga4Integration.id);
    }
    setSelectingProperty(false);
    setNeedsPropertySelection(false);
    setAvailableProperties([]);
    handleSync();
  }

  async function handleSync() {
    if (!brand) return;
    setSyncing(true);
    try {
      const res = await fetch("/api/analytics/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brand_id: brand.id }),
      });
      const data: SyncResponse = await res.json();
      if (res.ok) {
        await refreshSnapshots();
      } else if (data.properties && data.properties.length > 0) {
        setAvailableProperties(data.properties);
        setNeedsPropertySelection(true);
      } else {
        console.error("Sync failed:", data);
        alert(data.error || "Sync failed");
      }
    } catch (err) {
      console.error("Sync error:", err);
    }
    setSyncing(false);
  }

  async function handleSyncGsc() {
    if (!brand) return;
    setSyncingGsc(true);
    try {
      const res = await fetch("/api/analytics/sync-gsc", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brand_id: brand.id }),
      });
      const data: GscSyncResponse = await res.json();
      if (res.ok) {
        await refreshSnapshots();
      } else if (data.sites && data.sites.length > 0) {
        alert("Please select a Search Console site in Settings first.");
      } else {
        console.error("GSC sync failed:", data);
        alert(data.error || "GSC sync failed");
      }
    } catch (err) {
      console.error("GSC sync error:", err);
    }
    setSyncingGsc(false);
  }

  async function handleSyncAll() {
    if (!brand) return;
    setSyncingAll(true);
    const endpoints = connectedProviders
      .map((p) => SYNC_ENDPOINTS[p])
      .filter(Boolean);
    for (const endpoint of endpoints) {
      try {
        await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ brand_id: brand.id }),
        });
      } catch {
        // continue syncing other providers
      }
    }
    await refreshSnapshots();
    setSyncingAll(false);
  }

  if (brandLoading || snapshotLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24" />)}
        </div>
        <Skeleton className="h-80" />
      </div>
    );
  }

  // ---- Extract snapshot data per provider ----
  const gaSnap = getSnap(snapshots, "ga4");
  const gscSnap = getSnap(snapshots, "gsc");
  const fbSnap = getSnap(snapshots, "facebook");
  const igSnap = getSnap(snapshots, "instagram");
  const liSnap = getSnap(snapshots, "linkedin");
  const ytSnap = getSnap(snapshots, "youtube");
  const pinSnap = getSnap(snapshots, "pinterest");
  const gadsSnap = getSnap(snapshots, "google_ads");
  const metaSnap = getSnap(snapshots, "meta_ads");
  const mcSnap = getSnap(snapshots, "mailchimp");
  const sgSnap = getSnap(snapshots, "sendgrid");
  const klSnap = getSnap(snapshots, "klaviyo");
  const hsSnap = getSnap(snapshots, "hubspot");
  const stripeSnap = getSnap(snapshots, "stripe");
  const twitterSnap = getSnap(snapshots, "twitter");
  const ckSnap = getSnap(snapshots, "convertkit");
  const acSnap = getSnap(snapshots, "activecampaign");
  const calendlySnap = getSnap(snapshots, "calendly");
  const notionSnap = getSnap(snapshots, "notion");
  const sheetsSnap = getSnap(snapshots, "google_sheets");
  const airtableSnap = getSnap(snapshots, "airtable");
  const slackSnap = getSnap(snapshots, "slack");
  const webflowSnap = getSnap(snapshots, "webflow");
  const squarespaceSnap = getSnap(snapshots, "squarespace");
  const gbpSnap = getSnap(snapshots, "gbp");
  const wpSnap = getSnap(snapshots, "wordpress");
  const shopifySnap = getSnap(snapshots, "shopify");

  // ---- GA4 overview (existing) ----
  const overview = {
    sessions: (gaSnap?.sessions as number) || 0,
    users: (gaSnap?.users as number) || 0,
    pageviews: (gaSnap?.pageviews as number) || 0,
    bounceRate: (gaSnap?.bounce_rate as number) || 0,
    avgDuration: (gaSnap?.avg_session_duration as number) || 0,
    conversions: (gaSnap?.conversions as number) || 0,
  };

  const dailyData = (gaSnap?.daily as Array<{ date: string; sessions: number; users: number }>) || [];
  const topPages = (gaSnap?.top_pages as Array<{ path: string; views: number; avg_time: number; bounce_rate: number }>) || [];
  const sources = (gaSnap?.sources as Array<{ source: string; sessions: number; percentage: number }>) || [];
  const gscQueries = (gscSnap?.gsc_queries as Array<{ query: string; clicks: number; impressions: number; ctr: number; position: number }>) || [];

  const metrics = [
    { label: "Sessions", value: formatNumber(overview.sessions), icon: BarChart3, color: "text-amber" },
    { label: "Users", value: formatNumber(overview.users), icon: Users, color: "text-info" },
    { label: "Page Views", value: formatNumber(overview.pageviews), icon: Eye, color: "text-purple" },
    { label: "Conversions", value: formatNumber(overview.conversions), icon: TrendingUp, color: "text-success" },
  ];

  const noGaData = !gaSnap;

  // Section visibility
  const hasSocial = fbSnap || igSnap || liSnap || ytSnap || pinSnap || twitterSnap;
  const hasPaid = gadsSnap || metaSnap;
  const hasEmail = mcSnap || sgSnap || klSnap || ckSnap || acSnap;
  const hasCrm = hsSnap;
  const hasPayments = stripeSnap;
  const hasScheduling = calendlySnap;
  const hasContent = notionSnap || sheetsSnap || airtableSnap;
  const hasNotifications = slackSnap;
  const hasWebsite = webflowSnap || squarespaceSnap || wpSnap || shopifySnap;
  const hasLocal = gbpSnap;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight">Analytics</h1>
          <p className="text-text-secondary text-sm mt-1">Traffic, engagement, and marketing performance across all channels.</p>
        </div>
        <div className="flex items-center gap-3">
          {connectedProviders.length > 2 && (
            <Button variant="primary" size="sm" onClick={handleSyncAll} loading={syncingAll}>
              <RefreshCw className="w-3.5 h-3.5" />
              Sync All
            </Button>
          )}
          {gscConnected && (
            <Button variant="secondary" size="sm" onClick={handleSyncGsc} loading={syncingGsc}>
              <Search className="w-3.5 h-3.5" />
              Sync GSC
            </Button>
          )}
          {ga4Connected && (
            <Button variant="secondary" size="sm" onClick={handleSync} loading={syncing}>
              <RefreshCw className="w-3.5 h-3.5" />
              Sync GA4
            </Button>
          )}
          <div className="flex items-center gap-1 p-1 bg-bg-elevated rounded-lg border border-border">
            {["7d", "28d", "90d"].map((r) => (
              <button
                key={r}
                onClick={() => setRange(r)}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium rounded-md transition-colors",
                  range === r ? "bg-card text-foreground" : "text-text-secondary hover:text-foreground"
                )}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Property selection prompt */}
      {needsPropertySelection && availableProperties.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Select GA4 Property</CardTitle>
          </CardHeader>
          <p className="text-sm text-text-secondary mb-3">
            Multiple GA4 properties were found. Select the one to use for analytics.
          </p>
          <div className="space-y-2">
            {availableProperties.map((prop) => (
              <button
                key={prop.property_id}
                onClick={() => handleSelectProperty(prop.property_id)}
                disabled={selectingProperty}
                className="w-full flex items-center justify-between px-4 py-3 bg-bg-elevated rounded-lg hover:bg-card-hover transition-colors text-left disabled:opacity-50"
              >
                <div>
                  <p className="text-sm font-medium">{prop.display_name}</p>
                  <p className="text-xs text-text-tertiary">{prop.account_name} - {prop.property_id}</p>
                </div>
                <RefreshCw className={cn("w-4 h-4 text-text-tertiary", selectingProperty && "animate-spin")} />
              </button>
            ))}
          </div>
        </Card>
      )}

      {/* ============================================================ */}
      {/*  GA4 Section                                                  */}
      {/* ============================================================ */}

      {noGaData && !needsPropertySelection ? (
        <div className="flex flex-col items-center py-20 text-text-tertiary">
          <BarChart3 className="w-12 h-12 mb-3 opacity-30" />
          <p className="text-sm mb-2">No analytics data yet</p>
          {ga4Connected ? (
            <>
              <p className="text-xs mb-4">Google Analytics is connected. Pull your data now.</p>
              <Button onClick={handleSync} loading={syncing}>
                <RefreshCw className="w-4 h-4" />
                Sync Analytics
              </Button>
            </>
          ) : (
            <>
              <p className="text-xs">Connect Google Analytics to see your traffic data here.</p>
              <a href="/connect" className="text-amber text-sm mt-4 hover:underline">Connect accounts</a>
            </>
          )}
        </div>
      ) : !needsPropertySelection && gaSnap ? (
        <>
          {/* Metric cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {metrics.map((m) => (
              <Card key={m.label}>
                <div className="flex items-center gap-2 mb-2">
                  <m.icon className={cn("w-4 h-4", m.color)} />
                  <span className="text-xs text-text-secondary">{m.label}</span>
                </div>
                <p className="stat-number">{m.value}</p>
              </Card>
            ))}
          </div>

          {/* Traffic chart */}
          {dailyData.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Sessions Over Time</CardTitle>
              </CardHeader>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={dailyData}>
                    <CartesianGrid stroke="#1e1e1e" strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fill: "#6b6b6b", fontSize: 11 }} tickLine={false} axisLine={{ stroke: "#1e1e1e" }} />
                    <YAxis tick={{ fill: "#6b6b6b", fontSize: 11 }} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#141414", border: "1px solid #1e1e1e", borderRadius: "8px", fontSize: "12px" }} />
                    <Line type="monotone" dataKey="sessions" stroke="#f59e0b" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="users" stroke="#3b82f6" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {topPages.length > 0 && (
              <Card>
                <CardHeader><CardTitle>Top Pages</CardTitle></CardHeader>
                <div className="space-y-2">
                  {topPages.slice(0, 10).map((page, i) => (
                    <div key={i} className="flex items-center gap-3 px-2 py-1.5 rounded-lg hover:bg-bg-elevated">
                      <span className="text-xs text-text-tertiary font-mono w-5">{i + 1}</span>
                      <span className="text-sm flex-1 truncate">{page.path}</span>
                      <span className="text-xs font-mono text-text-secondary">{formatNumber(page.views)}</span>
                    </div>
                  ))}
                </div>
              </Card>
            )}
            {sources.length > 0 && (
              <Card>
                <CardHeader><CardTitle>Traffic Sources</CardTitle></CardHeader>
                <div className="space-y-3">
                  {sources.slice(0, 8).map((src, i) => (
                    <div key={i} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-text-secondary">{src.source}</span>
                        <span className="font-mono">{formatNumber(src.sessions)}</span>
                      </div>
                      <div className="h-1.5 bg-border rounded-full overflow-hidden">
                        <div className="h-full bg-amber rounded-full" style={{ width: `${src.percentage}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        </>
      ) : null}

      {/* ============================================================ */}
      {/*  GSC Section                                                  */}
      {/* ============================================================ */}

      {gscQueries.length > 0 ? (
        <Card>
          <CardHeader><CardTitle>Search Queries</CardTitle></CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2 px-3 text-xs text-text-tertiary font-medium">Query</th>
                  <th className="text-right py-2 px-3 text-xs text-text-tertiary font-medium">Clicks</th>
                  <th className="text-right py-2 px-3 text-xs text-text-tertiary font-medium">Impressions</th>
                  <th className="text-right py-2 px-3 text-xs text-text-tertiary font-medium">CTR</th>
                  <th className="text-right py-2 px-3 text-xs text-text-tertiary font-medium">Position</th>
                </tr>
              </thead>
              <tbody>
                {gscQueries.slice(0, 20).map((q, i) => (
                  <tr key={i} className="border-b border-border/50 hover:bg-bg-elevated">
                    <td className="py-2.5 px-3 truncate max-w-[200px]">{q.query}</td>
                    <td className="py-2.5 px-3 text-right font-mono text-xs">{formatNumber(q.clicks)}</td>
                    <td className="py-2.5 px-3 text-right font-mono text-xs">{formatNumber(q.impressions)}</td>
                    <td className="py-2.5 px-3 text-right font-mono text-xs">{formatPercent(q.ctr)}</td>
                    <td className={cn(
                      "py-2.5 px-3 text-right font-mono text-xs",
                      q.position < 10 ? "text-success" : q.position < 20 ? "text-amber" : "text-error"
                    )}>
                      {q.position.toFixed(1)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : gscConnected ? (
        <Card>
          <div className="flex flex-col items-center py-8 text-text-tertiary">
            <Search className="w-8 h-8 mb-2 opacity-30" />
            <p className="text-sm mb-1">No search query data yet</p>
            <p className="text-xs mb-3">Sync Google Search Console to see your search performance.</p>
            <Button variant="secondary" size="sm" onClick={handleSyncGsc} loading={syncingGsc}>
              <Search className="w-3.5 h-3.5" />
              Sync GSC
            </Button>
          </div>
        </Card>
      ) : null}

      {/* ============================================================ */}
      {/*  Social Media                                                 */}
      {/* ============================================================ */}

      {hasSocial && (
        <Section title="Social Media">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {fbSnap && (
              <MetricCard icon={Facebook} name="Facebook" color="text-blue-500" metrics={[
                { label: "Followers", value: formatNumber(fbSnap.followers as number) },
                { label: "Impressions", value: formatNumber(fbSnap.impressions as number) },
                { label: "Engaged Users", value: formatNumber(fbSnap.engaged_users as number) },
                { label: "Page Views", value: formatNumber(fbSnap.page_views as number) },
              ]} />
            )}
            {igSnap && (
              <MetricCard icon={Instagram} name="Instagram" color="text-pink-500" metrics={[
                { label: "Followers", value: formatNumber(igSnap.followers as number) },
                { label: "Impressions", value: formatNumber(igSnap.impressions as number) },
                { label: "Reach", value: formatNumber(igSnap.reach as number) },
                { label: "Profile Views", value: formatNumber(igSnap.profile_views as number) },
              ]} />
            )}
            {liSnap && (
              <MetricCard icon={Linkedin} name="LinkedIn" color="text-blue-600" metrics={[
                { label: "Followers", value: formatNumber(liSnap.followers as number) },
                { label: "Impressions", value: formatNumber(liSnap.impressions as number) },
                { label: "Clicks", value: formatNumber(liSnap.clicks as number) },
                { label: "Engagement", value: formatPercent((liSnap.engagement_rate as number) || 0) },
              ]} />
            )}
            {ytSnap && (
              <MetricCard icon={Youtube} name="YouTube" color="text-red-500" metrics={[
                { label: "Subscribers", value: formatNumber(ytSnap.subscribers as number) },
                { label: "Total Views", value: formatNumber(ytSnap.total_views as number) },
                { label: "Videos", value: formatNumber(ytSnap.video_count as number) },
              ]} />
            )}
            {pinSnap && (
              <MetricCard icon={Pin} name="Pinterest" color="text-red-600" metrics={[
                { label: "Followers", value: formatNumber(pinSnap.followers as number) },
                { label: "Impressions", value: formatNumber(pinSnap.impressions as number) },
                { label: "Saves", value: formatNumber(pinSnap.saves as number) },
                { label: "Pin Clicks", value: formatNumber(pinSnap.pin_clicks as number) },
              ]} />
            )}
            {twitterSnap && (
              <MetricCard icon={Twitter} name="X / Twitter" color="text-gray-400" metrics={[
                { label: "Followers", value: formatNumber(twitterSnap.followers as number) },
                { label: "Tweets", value: formatNumber(twitterSnap.tweet_count as number) },
                { label: "Following", value: formatNumber(twitterSnap.following as number) },
                { label: "Listed", value: formatNumber(twitterSnap.listed_count as number) },
              ]} />
            )}
          </div>
        </Section>
      )}

      {/* ============================================================ */}
      {/*  Paid Media                                                   */}
      {/* ============================================================ */}

      {hasPaid && (
        <Section title="Paid Media">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {gadsSnap && (
              <MetricCard icon={Megaphone} name="Google Ads" color="text-amber" metrics={[
                { label: "Impressions", value: formatNumber(gadsSnap.impressions as number) },
                { label: "Clicks", value: formatNumber(gadsSnap.clicks as number) },
                { label: "Cost", value: formatDollar(gadsSnap.cost as number) },
                { label: "Conversions", value: formatNumber(gadsSnap.conversions as number) },
                { label: "CTR", value: formatPercent(gadsSnap.ctr as number) },
                { label: "Avg CPC", value: formatDollar(gadsSnap.avg_cpc as number) },
              ]} />
            )}
            {metaSnap && (
              <MetricCard icon={Target} name="Meta Ads" color="text-blue-500" metrics={[
                { label: "Spend", value: formatDollar(metaSnap.spend as number) },
                { label: "Impressions", value: formatNumber(metaSnap.impressions as number) },
                { label: "Clicks", value: formatNumber(metaSnap.clicks as number) },
                { label: "Conversions", value: formatNumber(metaSnap.conversions as number) },
                { label: "CPM", value: formatDollar(metaSnap.cpm as number) },
                { label: "ROAS", value: ((metaSnap.roas as number) || 0).toFixed(2) + "x" },
              ]} />
            )}
          </div>
        </Section>
      )}

      {/* ============================================================ */}
      {/*  Email                                                        */}
      {/* ============================================================ */}

      {hasEmail && (
        <Section title="Email">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {mcSnap && (
              <MetricCard icon={Mail} name="Mailchimp" color="text-yellow-500" metrics={[
                { label: "Subscribers", value: formatNumber(mcSnap.total_subscribers as number) },
                { label: "Open Rate", value: formatPercent(mcSnap.avg_open_rate as number) },
                { label: "Click Rate", value: formatPercent(mcSnap.avg_click_rate as number) },
                { label: "Audiences", value: formatNumber(mcSnap.audience_count as number) },
              ]} />
            )}
            {sgSnap && (
              <MetricCard icon={Send} name="SendGrid" color="text-blue-400" metrics={[
                { label: "Delivered", value: formatNumber(sgSnap.delivered as number) },
                { label: "Opens", value: formatNumber(sgSnap.opens as number) },
                { label: "Clicks", value: formatNumber(sgSnap.clicks as number) },
                { label: "Bounces", value: formatNumber(sgSnap.bounces as number) },
              ]} />
            )}
            {klSnap && (
              <MetricCard icon={Zap} name="Klaviyo" color="text-green-500" metrics={[
                { label: "Subscribers", value: formatNumber(klSnap.total_subscribers as number) },
                { label: "Lists", value: formatNumber(klSnap.list_count as number) },
              ]} />
            )}
            {ckSnap && (
              <MetricCard icon={UserCheck} name="ConvertKit" color="text-red-400" metrics={[
                { label: "Subscribers", value: formatNumber(ckSnap.subscriber_count as number) },
                { label: "Sequences", value: formatNumber(ckSnap.sequences_count as number) },
                { label: "Automations", value: formatNumber(ckSnap.automations_count as number) },
              ]} />
            )}
            {acSnap && (
              <MetricCard icon={Send} name="ActiveCampaign" color="text-blue-500" metrics={[
                { label: "Contacts", value: formatNumber(acSnap.contacts_count as number) },
                { label: "Campaigns", value: formatNumber(acSnap.campaigns_count as number) },
                { label: "Deals", value: formatNumber(acSnap.deals_count as number) },
                { label: "Automations", value: formatNumber(acSnap.automations_count as number) },
              ]} />
            )}
          </div>
        </Section>
      )}

      {/* ============================================================ */}
      {/*  CRM                                                          */}
      {/* ============================================================ */}

      {hasCrm && (
        <Section title="CRM">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {hsSnap && (
              <MetricCard icon={UserCheck} name="HubSpot" color="text-orange-500" metrics={[
                { label: "Contacts", value: formatNumber(hsSnap.contacts_count as number) },
                { label: "Deals", value: formatNumber(hsSnap.deals_count as number) },
                { label: "Deal Value", value: formatDollar(hsSnap.deals_total_value as number) },
                { label: "Companies", value: formatNumber(hsSnap.companies_count as number) },
              ]} />
            )}
          </div>
        </Section>
      )}

      {/* ============================================================ */}
      {/*  Payments                                                     */}
      {/* ============================================================ */}

      {hasPayments && (
        <Section title="Payments">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {stripeSnap && (
              <MetricCard icon={CreditCard} name="Stripe" color="text-purple" metrics={[
                { label: "MRR", value: formatDollar(stripeSnap.mrr as number) },
                { label: "Revenue (28d)", value: formatDollar(stripeSnap.total_revenue_28d as number) },
                { label: "Active Subs", value: formatNumber(stripeSnap.active_subscriptions as number) },
              ]} />
            )}
          </div>
        </Section>
      )}

      {/* ============================================================ */}
      {/*  Scheduling                                                   */}
      {/* ============================================================ */}

      {hasScheduling && (
        <Section title="Scheduling">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {calendlySnap && (
              <MetricCard icon={Calendar} name="Calendly" color="text-blue-500" metrics={[
                { label: "Upcoming", value: formatNumber(calendlySnap.upcoming_events as number) },
                { label: "Events (30d)", value: formatNumber(calendlySnap.total_events_30d as number) },
              ]} />
            )}
          </div>
        </Section>
      )}

      {/* ============================================================ */}
      {/*  Content Tools                                                */}
      {/* ============================================================ */}

      {hasContent && (
        <Section title="Content Tools">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {notionSnap && (
              <MetricCard icon={BookOpen} name="Notion" color="text-gray-300" metrics={[
                { label: "Databases", value: formatNumber(notionSnap.databases_count as number) },
                { label: "Pages", value: formatNumber(notionSnap.pages_count as number) },
              ]} />
            )}
            {sheetsSnap && (
              <MetricCard icon={Table2} name="Google Sheets" color="text-green-500" metrics={[
                { label: "Spreadsheets", value: formatNumber(sheetsSnap.spreadsheets_count as number) },
              ]} />
            )}
            {airtableSnap && (
              <MetricCard icon={Table2} name="Airtable" color="text-blue-400" metrics={[
                { label: "Bases", value: formatNumber(airtableSnap.bases_count as number) },
              ]} />
            )}
          </div>
        </Section>
      )}

      {/* ============================================================ */}
      {/*  Website                                                      */}
      {/* ============================================================ */}

      {hasWebsite && (
        <Section title="Website">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {webflowSnap && (
              <MetricCard icon={Layout} name="Webflow" color="text-blue-500" metrics={[
                { label: "Sites", value: formatNumber(webflowSnap.sites_count as number) },
                { label: "Pages", value: formatNumber(webflowSnap.total_pages as number) },
                { label: "Collections", value: formatNumber(webflowSnap.total_collections as number) },
              ]} />
            )}
            {squarespaceSnap && (
              <MetricCard icon={SquareCode} name="Squarespace" color="text-gray-300" metrics={[
                { label: "Products", value: formatNumber(squarespaceSnap.products_count as number) },
                { label: "Orders (30d)", value: formatNumber(squarespaceSnap.orders_count_30d as number) },
              ]} />
            )}
            {wpSnap && (
              <MetricCard icon={Globe} name="WordPress" color="text-blue-400" metrics={[
                { label: "Posts", value: formatNumber(wpSnap.posts_count as number) },
                { label: "Pages", value: formatNumber(wpSnap.pages_count as number) },
              ]} />
            )}
            {shopifySnap && (
              <MetricCard icon={ShoppingBag} name="Shopify" color="text-green-500" metrics={[
                { label: "Products", value: formatNumber(shopifySnap.products_count as number) },
                { label: "Orders (30d)", value: formatNumber(shopifySnap.orders_count_30d as number) },
              ]} />
            )}
          </div>
        </Section>
      )}

      {/* ============================================================ */}
      {/*  Notifications                                                */}
      {/* ============================================================ */}

      {hasNotifications && (
        <Section title="Notifications">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {slackSnap && (
              <MetricCard icon={MessageSquare} name={`Slack — ${slackSnap.workspace_name || "Workspace"}`} color="text-purple" metrics={[
                { label: "Members", value: formatNumber(slackSnap.members_count as number) },
                { label: "Channels", value: formatNumber(slackSnap.channels_count as number) },
              ]} />
            )}
          </div>
        </Section>
      )}

      {/* ============================================================ */}
      {/*  Local / Google Business                                      */}
      {/* ============================================================ */}

      {hasLocal && (
        <Section title="Local / Google Business">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {gbpSnap && (
              <MetricCard icon={MapPin} name="Google Business Profile" color="text-blue-500" metrics={[
                { label: "Accounts", value: formatNumber(gbpSnap.accounts_count as number) },
                { label: "Locations", value: formatNumber(gbpSnap.locations_count as number) },
              ]} />
            )}
          </div>
        </Section>
      )}
    </div>
  );
}
