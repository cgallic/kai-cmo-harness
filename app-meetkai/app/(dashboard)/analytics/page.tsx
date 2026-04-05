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
import { BarChart3, TrendingUp, Users, Eye, RefreshCw, Search } from "lucide-react";
import { createClient } from "@/lib/supabase/client";

interface GA4Property {
  property_id: string;
  display_name: string;
  account_name: string;
}

interface GscSite {
  site_url: string;
  permission_level: string;
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
  sites?: GscSite[];
  data?: Record<string, unknown>;
}

export default function AnalyticsPage() {
  const { brand, loading: brandLoading } = useBrand();
  const { snapshots, loading: snapshotLoading, refresh: refreshSnapshots } = useSnapshots(brand?.id, "analytics");
  const { integrations } = useIntegrations(brand?.id);
  const [range, setRange] = useState("28d");
  const [syncing, setSyncing] = useState(false);
  const [syncingGsc, setSyncingGsc] = useState(false);
  const [needsPropertySelection, setNeedsPropertySelection] = useState(false);
  const [availableProperties, setAvailableProperties] = useState<GA4Property[]>([]);
  const [selectingProperty, setSelectingProperty] = useState(false);

  const ga4Connected = integrations.some((i) => i.provider === "ga4" && i.status === "connected");
  const gscConnected = integrations.some(
    (i) => i.provider === "google_search_console" && i.status === "connected"
  );

  async function handleSelectProperty(propertyId: string) {
    if (!brand) return;
    setSelectingProperty(true);
    const supabase = createClient();
    const ga4Integration = integrations.find(
      (i) => i.provider === "ga4" && i.status === "connected"
    );
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
    // Auto-trigger sync after selection
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
        // Backend is asking user to select a GA4 property
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

  // Extract latest GA4 snapshot data
  const gaSnapshot = snapshots.find((s) => s.provider === "ga4");
  const data = (gaSnapshot?.snapshot_data || {}) as Record<string, unknown>;

  // Extract latest GSC snapshot data (stored separately)
  const gscSnapshot = snapshots.find((s) => s.provider === "gsc");
  const gscData = (gscSnapshot?.snapshot_data || {}) as Record<string, unknown>;

  const overview = {
    sessions: (data.sessions as number) || 0,
    users: (data.users as number) || 0,
    pageviews: (data.pageviews as number) || 0,
    bounceRate: (data.bounce_rate as number) || 0,
    avgDuration: (data.avg_session_duration as number) || 0,
    conversions: (data.conversions as number) || 0,
  };

  const dailyData = (data.daily as Array<{ date: string; sessions: number; users: number }>) || [];
  const topPages = (data.top_pages as Array<{ path: string; views: number; avg_time: number; bounce_rate: number }>) || [];
  const sources = (data.sources as Array<{ source: string; sessions: number; percentage: number }>) || [];
  const gscQueries = (gscData.gsc_queries as Array<{ query: string; clicks: number; impressions: number; ctr: number; position: number }>) || [];

  const metrics = [
    { label: "Sessions", value: formatNumber(overview.sessions), icon: BarChart3, color: "text-amber" },
    { label: "Users", value: formatNumber(overview.users), icon: Users, color: "text-info" },
    { label: "Page Views", value: formatNumber(overview.pageviews), icon: Eye, color: "text-purple" },
    { label: "Conversions", value: formatNumber(overview.conversions), icon: TrendingUp, color: "text-success" },
  ];

  const noData = snapshots.length === 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight">Analytics</h1>
          <p className="text-text-secondary text-sm mt-1">Traffic, engagement, and search performance.</p>
        </div>
        <div className="flex items-center gap-3">
          {gscConnected && (
            <Button variant="secondary" size="sm" onClick={handleSyncGsc} loading={syncingGsc}>
              <Search className="w-3.5 h-3.5" />
              Sync GSC
            </Button>
          )}
          {ga4Connected && (
            <Button variant="secondary" size="sm" onClick={handleSync} loading={syncing}>
              <RefreshCw className="w-3.5 h-3.5" />
              Sync
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

      {noData && !needsPropertySelection ? (
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
      ) : !needsPropertySelection ? (
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
                    <XAxis
                      dataKey="date"
                      tick={{ fill: "#6b6b6b", fontSize: 11 }}
                      tickLine={false}
                      axisLine={{ stroke: "#1e1e1e" }}
                    />
                    <YAxis
                      tick={{ fill: "#6b6b6b", fontSize: 11 }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "#141414",
                        border: "1px solid #1e1e1e",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                    />
                    <Line type="monotone" dataKey="sessions" stroke="#f59e0b" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="users" stroke="#3b82f6" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Pages */}
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

            {/* Traffic Sources */}
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
                        <div
                          className="h-full bg-amber rounded-full"
                          style={{ width: `${src.percentage}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>

          {/* GSC Queries */}
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
        </>
      ) : null}
    </div>
  );
}
