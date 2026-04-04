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

type GaRow = {
  dimensionValues?: { value: string }[];
  metricValues: { value: string }[];
};

async function ga4Report(pd: PipedreamClient, accountId: string, brandId: string, propertyId: string, body: Record<string, unknown>) {
  const res = await pd.proxy.post({
    url: `https://analyticsdata.googleapis.com/v1beta/${propertyId}:runReport`,
    accountId,
    externalUserId: brandId,
    body,
  });
  return (res as { data?: unknown })?.data ?? res;
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
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
    .eq("provider", "ga4")
    .eq("status", "connected")
    .single();

  if (!integration?.connected_account_id) {
    return NextResponse.json({ error: "Google Analytics not connected" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;

  try {
    const pd = getPd();

    // 1. Find GA4 property
    const adminRes = await pd.proxy.get({
      url: "https://analyticsadmin.googleapis.com/v1beta/accountSummaries",
      accountId,
      externalUserId: brand_id,
    });
    const adminData = (adminRes as { data?: { accountSummaries?: { propertySummaries?: { property: string }[] }[] } })?.data ?? adminRes;
    console.log("GA4 admin:", JSON.stringify(adminData).slice(0, 300));

    let propertyId: string | null = null;
    const summaries = (adminData as { accountSummaries?: { propertySummaries?: { property: string }[] }[] })?.accountSummaries;
    if (summaries) {
      for (const acct of summaries) {
        if (acct.propertySummaries?.length) {
          propertyId = acct.propertySummaries[0].property;
          break;
        }
      }
    }

    if (!propertyId) {
      return NextResponse.json({ error: "No GA4 properties found" }, { status: 404 });
    }
    console.log("Using property:", propertyId);

    // 2. Overview metrics
    const overviewReport = await ga4Report(pd, accountId, brand_id, propertyId, {
      dateRanges: [{ startDate: "28daysAgo", endDate: "today" }],
      metrics: [
        { name: "sessions" },
        { name: "totalUsers" },
        { name: "screenPageViews" },
        { name: "bounceRate" },
        { name: "averageSessionDuration" },
        { name: "conversions" },
      ],
    }) as { rows?: GaRow[] };

    const mv = overviewReport?.rows?.[0]?.metricValues || [];
    const overview = {
      sessions: parseInt(mv[0]?.value || "0"),
      users: parseInt(mv[1]?.value || "0"),
      pageviews: parseInt(mv[2]?.value || "0"),
      bounce_rate: Math.round(parseFloat(mv[3]?.value || "0") * 100),
      avg_session_duration: Math.round(parseFloat(mv[4]?.value || "0")),
      conversions: parseInt(mv[5]?.value || "0"),
    };

    // 3. Daily data
    const dailyReport = await ga4Report(pd, accountId, brand_id, propertyId, {
      dateRanges: [{ startDate: "28daysAgo", endDate: "today" }],
      dimensions: [{ name: "date" }],
      metrics: [{ name: "sessions" }, { name: "totalUsers" }],
      orderBys: [{ dimension: { dimensionName: "date" } }],
    }) as { rows?: GaRow[] };

    const daily = (dailyReport?.rows || []).map((r: GaRow) => ({
      date: (r.dimensionValues?.[0]?.value || "").replace(/(\d{4})(\d{2})(\d{2})/, "$1-$2-$3"),
      sessions: parseInt(r.metricValues[0].value),
      users: parseInt(r.metricValues[1].value),
    }));

    // 4. Top pages
    const pagesReport = await ga4Report(pd, accountId, brand_id, propertyId, {
      dateRanges: [{ startDate: "28daysAgo", endDate: "today" }],
      dimensions: [{ name: "pagePath" }],
      metrics: [{ name: "screenPageViews" }, { name: "averageSessionDuration" }, { name: "bounceRate" }],
      orderBys: [{ metric: { metricName: "screenPageViews" }, desc: true }],
      limit: "10",
    }) as { rows?: GaRow[] };

    const top_pages = (pagesReport?.rows || []).map((r: GaRow) => ({
      path: r.dimensionValues?.[0]?.value || "/",
      views: parseInt(r.metricValues[0].value),
      avg_time: Math.round(parseFloat(r.metricValues[1].value)),
      bounce_rate: Math.round(parseFloat(r.metricValues[2].value) * 100),
    }));

    // 5. Traffic sources
    const sourcesReport = await ga4Report(pd, accountId, brand_id, propertyId, {
      dateRanges: [{ startDate: "28daysAgo", endDate: "today" }],
      dimensions: [{ name: "sessionSource" }],
      metrics: [{ name: "sessions" }],
      orderBys: [{ metric: { metricName: "sessions" }, desc: true }],
      limit: "10",
    }) as { rows?: GaRow[] };

    const totalSessions = overview.sessions || 1;
    const sources = (sourcesReport?.rows || []).map((r: GaRow) => ({
      source: r.dimensionValues?.[0]?.value || "(direct)",
      sessions: parseInt(r.metricValues[0].value),
      percentage: Math.round((parseInt(r.metricValues[0].value) / totalSessions) * 100),
    }));

    // Save snapshot
    const snapshot = { ...overview, daily, top_pages, sources };
    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "analytics",
      provider: "ga4",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("GA4 sync error:", message);
    return NextResponse.json({ error: "Sync failed", detail: message }, { status: 502 });
  }
}
