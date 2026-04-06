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

interface SendGridDayMetrics {
  delivered: number;
  opens: number;
  unique_opens: number;
  clicks: number;
  unique_clicks: number;
  bounces: number;
  spam_reports: number;
  requests: number;
}

interface SendGridStatEntry {
  date: string;
  stats: Array<{
    metrics: SendGridDayMetrics;
  }>;
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

  const { data: integrations } = await serviceClient
    .from("integrations")
    .select("*")
    .eq("brand_id", brand_id)
    .eq("provider", "sendgrid")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "SendGrid not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "SendGrid not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;

  try {
    const pd = getPd();

    // Build date range: last 28 days
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 28);

    const fmt = (d: Date) => d.toISOString().slice(0, 10); // YYYY-MM-DD

    // Fetch global stats aggregated by day
    const statsRes = await pd.proxy.get({
      url: `https://api.sendgrid.com/v3/stats?start_date=${fmt(startDate)}&end_date=${fmt(endDate)}&aggregated_by=day`,
      accountId,
      externalUserId: brand_id,
    });

    const statsData = ((statsRes as { data?: SendGridStatEntry[] })?.data ?? statsRes) as SendGridStatEntry[];
    const entries = Array.isArray(statsData) ? statsData : [];

    // Aggregate totals across all days
    let delivered = 0;
    let opens = 0;
    let uniqueOpens = 0;
    let clicks = 0;
    let uniqueClicks = 0;
    let bounces = 0;
    let spamReports = 0;
    let requests = 0;

    const daily: Array<{ date: string; delivered: number; opens: number; clicks: number }> = [];

    for (const entry of entries) {
      // Each day can have multiple stat buckets; sum them
      let dayDelivered = 0;
      let dayOpens = 0;
      let dayClicks = 0;

      for (const s of entry.stats) {
        const m = s.metrics;
        delivered += m.delivered;
        opens += m.opens;
        uniqueOpens += m.unique_opens;
        clicks += m.clicks;
        uniqueClicks += m.unique_clicks;
        bounces += m.bounces;
        spamReports += m.spam_reports;
        requests += m.requests;

        dayDelivered += m.delivered;
        dayOpens += m.opens;
        dayClicks += m.clicks;
      }

      daily.push({
        date: entry.date,
        delivered: dayDelivered,
        opens: dayOpens,
        clicks: dayClicks,
      });
    }

    const snapshot = {
      delivered,
      opens,
      unique_opens: uniqueOpens,
      clicks,
      unique_clicks: uniqueClicks,
      bounces,
      spam_reports: spamReports,
      requests,
      daily,
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "email",
      provider: "sendgrid",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("SendGrid sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
