import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import { PipedreamClient } from "@pipedream/sdk";

function getPd() {
  return new PipedreamClient({
    projectId: process.env.PIPEDREAM_PROJECT_ID!,
    projectEnvironment:
      (process.env.PIPEDREAM_ENVIRONMENT as "development" | "production") || "development",
    clientId: process.env.PIPEDREAM_CLIENT_ID!,
    clientSecret: process.env.PIPEDREAM_CLIENT_SECRET!,
  });
}

interface GscRow {
  keys: string[];
  clicks: number;
  impressions: number;
  ctr: number;
  position: number;
}

interface GscQueryResponse {
  rows?: GscRow[];
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { brand_id } = await request.json();

  const { data: brand } = await supabase
    .from("brands")
    .select("id")
    .eq("id", brand_id)
    .eq("user_id", user.id)
    .single();

  if (!brand) {
    return NextResponse.json({ error: "Brand not found" }, { status: 404 });
  }

  const serviceClient = await createServiceClient();

  const { data: integration } = await serviceClient
    .from("integrations")
    .select("*")
    .eq("brand_id", brand_id)
    .eq("provider", "google_search_console")
    .eq("status", "connected")
    .single();

  if (!integration?.connected_account_id) {
    return NextResponse.json(
      { error: "Google Search Console not connected" },
      { status: 404 }
    );
  }

  const config = (integration.config || {}) as Record<string, unknown>;
  const siteUrl = config.gsc_site_url as string | undefined;

  if (!siteUrl) {
    // Return available sites so frontend can prompt for selection
    try {
      const pd = getPd();
      const res = await pd.proxy.get({
        url: "https://www.googleapis.com/webmasters/v3/sites",
        accountId: integration.connected_account_id,
        externalUserId: brand_id,
      });

      const data = (
        (res as { data?: { siteEntry?: { siteUrl: string; permissionLevel: string }[] } })?.data ?? res
      ) as { siteEntry?: { siteUrl: string; permissionLevel: string }[] };

      const sites = (data?.siteEntry || []).map((entry) => ({
        site_url: entry.siteUrl,
        permission_level: entry.permissionLevel,
      }));

      return NextResponse.json({
        error: "No GSC site selected",
        sites,
      });
    } catch {
      return NextResponse.json(
        { error: "No GSC site selected and could not fetch sites" },
        { status: 400 }
      );
    }
  }

  try {
    const pd = getPd();
    const accountId = integration.connected_account_id;

    const today = new Date();
    const endDate = new Date(today);
    endDate.setDate(endDate.getDate() - 3); // GSC data lags ~3 days
    const startDate = new Date(endDate);
    startDate.setDate(startDate.getDate() - 28);

    const formatDate = (d: Date) => d.toISOString().split("T")[0];

    const encodedSiteUrl = encodeURIComponent(siteUrl);
    const queryRes = await pd.proxy.post({
      url: `https://www.googleapis.com/webmasters/v3/sites/${encodedSiteUrl}/searchAnalytics/query`,
      accountId,
      externalUserId: brand_id,
      body: {
        startDate: formatDate(startDate),
        endDate: formatDate(endDate),
        dimensions: ["query"],
        rowLimit: 25,
      },
    });

    const queryData = ((queryRes as { data?: GscQueryResponse })?.data ??
      queryRes) as GscQueryResponse;

    const gscQueries = (queryData?.rows || []).map((row) => ({
      query: row.keys[0],
      clicks: row.clicks,
      impressions: row.impressions,
      ctr: Math.round(row.ctr * 1000) / 10, // Convert to percentage with 1 decimal
      position: Math.round(row.position * 10) / 10,
    }));

    // Save snapshot
    const snapshot = { gsc_queries: gscQueries };
    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "analytics",
      provider: "gsc",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("GSC sync error:", message);
    return NextResponse.json(
      { error: "GSC sync failed", detail: message },
      { status: 502 }
    );
  }
}
