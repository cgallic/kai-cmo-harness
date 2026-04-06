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

interface PinterestUserAccount {
  username?: string;
  follower_count?: number;
}

interface PinterestAnalytics {
  all?: {
    daily_metrics?: PinterestDailyMetric[];
  };
}

interface PinterestDailyMetric {
  data_status?: string;
  date?: string;
  metrics?: {
    IMPRESSION?: number;
    SAVE?: number;
    PIN_CLICK?: number;
    OUTBOUND_CLICK?: number;
  };
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
    .eq("provider", "pinterest")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "Pinterest not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "Pinterest not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;

  try {
    const pd = getPd();

    // Build date range for 28-day analytics window
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - 28);
    const startStr = startDate.toISOString().split("T")[0];
    const endStr = endDate.toISOString().split("T")[0];

    // Fetch user account info (username, follower count)
    const userRes = await pd.proxy.get({
      url: "https://api.pinterest.com/v5/user_account",
      accountId,
      externalUserId: brand_id,
    });

    const userAccount = ((userRes as { data?: PinterestUserAccount })?.data ?? userRes) as PinterestUserAccount;

    // Fetch user account analytics (28-day window)
    const analyticsRes = await pd.proxy.get({
      url: `https://api.pinterest.com/v5/user_account/analytics?start_date=${startStr}&end_date=${endStr}&metric_types=IMPRESSION,SAVE,PIN_CLICK,OUTBOUND_CLICK`,
      accountId,
      externalUserId: brand_id,
    });

    const analyticsData = ((analyticsRes as { data?: PinterestAnalytics })?.data ?? analyticsRes) as PinterestAnalytics;

    // Sum daily metrics across the 28-day window
    const dailyMetrics = analyticsData?.all?.daily_metrics || [];
    let impressions = 0;
    let saves = 0;
    let pinClicks = 0;
    let outboundClicks = 0;

    for (const day of dailyMetrics) {
      impressions += day.metrics?.IMPRESSION ?? 0;
      saves += day.metrics?.SAVE ?? 0;
      pinClicks += day.metrics?.PIN_CLICK ?? 0;
      outboundClicks += day.metrics?.OUTBOUND_CLICK ?? 0;
    }

    const snapshot = {
      username: userAccount.username || "unknown",
      followers: userAccount.follower_count ?? 0,
      impressions,
      saves,
      pin_clicks: pinClicks,
      outbound_clicks: outboundClicks,
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "social",
      provider: "pinterest",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Pinterest sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
