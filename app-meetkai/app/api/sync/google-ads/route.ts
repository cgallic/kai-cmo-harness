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

interface GoogleAdsRow {
  metrics: {
    impressions: string;
    clicks: string;
    costMicros: string;
    conversions: string;
    ctr: string;
    averageCpc: string;
  };
  campaign?: {
    name: string;
    status: string;
  };
}

interface GoogleAdsResponse {
  results?: GoogleAdsRow[];
}

interface AccessibleCustomersResponse {
  resourceNames?: string[];
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
    .eq("provider", "google_ads")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "Google Ads not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "Google Ads not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;
  const config = (integration.config || {}) as Record<string, string>;
  const customerId = config.google_ads_customer_id?.replace(/-/g, "");

  if (!customerId) {
    // Fetch accessible customers so user can pick one
    try {
      const pd = getPd();
      const res = await pd.proxy.get({
        url: "https://googleads.googleapis.com/v16/customers:listAccessibleCustomers",
        accountId,
        externalUserId: brand_id,
      });

      const data = ((res as { data?: AccessibleCustomersResponse })?.data ?? res) as AccessibleCustomersResponse;
      const customers = (data?.resourceNames || []).map((rn) => ({
        customer_id: rn.replace("customers/", ""),
      }));

      return NextResponse.json({
        error: "No Google Ads customer ID configured",
        code: "NO_CUSTOMER_ID",
        customers,
      });
    } catch {
      return NextResponse.json({ error: "No customer ID configured" }, { status: 400 });
    }
  }

  try {
    const pd = getPd();

    // Fetch 28-day aggregate metrics
    const today = new Date();
    const startDate = new Date(today);
    startDate.setDate(startDate.getDate() - 28);
    const formatDate = (d: Date) => d.toISOString().split("T")[0];

    const overviewRes = await pd.proxy.post({
      url: `https://googleads.googleapis.com/v16/customers/${customerId}/googleAds:searchStream`,
      accountId,
      externalUserId: brand_id,
      headers: { "login-customer-id": customerId },
      body: {
        query: `SELECT metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions, metrics.ctr, metrics.average_cpc FROM customer WHERE segments.date BETWEEN '${formatDate(startDate)}' AND '${formatDate(today)}'`,
      },
    });

    const overviewData = ((overviewRes as { data?: GoogleAdsResponse[] })?.data ?? overviewRes) as GoogleAdsResponse[];
    const overviewResults = overviewData?.[0]?.results || [];
    const overviewRow = overviewResults[0]?.metrics;

    const overview = {
      impressions: parseInt(overviewRow?.impressions || "0"),
      clicks: parseInt(overviewRow?.clicks || "0"),
      cost: parseInt(overviewRow?.costMicros || "0") / 1_000_000,
      conversions: parseFloat(overviewRow?.conversions || "0"),
      ctr: Math.round(parseFloat(overviewRow?.ctr || "0") * 10000) / 100,
      avg_cpc: parseInt(overviewRow?.averageCpc || "0") / 1_000_000,
    };

    // Fetch per-campaign breakdown
    const campaignRes = await pd.proxy.post({
      url: `https://googleads.googleapis.com/v16/customers/${customerId}/googleAds:searchStream`,
      accountId,
      externalUserId: brand_id,
      headers: { "login-customer-id": customerId },
      body: {
        query: `SELECT campaign.name, campaign.status, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM campaign WHERE segments.date BETWEEN '${formatDate(startDate)}' AND '${formatDate(today)}' AND campaign.status = 'ENABLED' ORDER BY metrics.cost_micros DESC LIMIT 10`,
      },
    });

    const campaignData = ((campaignRes as { data?: GoogleAdsResponse[] })?.data ?? campaignRes) as GoogleAdsResponse[];
    const campaignResults = campaignData?.[0]?.results || [];

    const campaigns = campaignResults.map((r) => ({
      name: r.campaign?.name || "Unknown",
      status: r.campaign?.status || "UNKNOWN",
      impressions: parseInt(r.metrics.impressions || "0"),
      clicks: parseInt(r.metrics.clicks || "0"),
      cost: parseInt(r.metrics.costMicros || "0") / 1_000_000,
      conversions: parseFloat(r.metrics.conversions || "0"),
    }));

    const snapshot = { ...overview, campaigns };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "paid_media",
      provider: "google_ads",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Google Ads sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
