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

interface MetaAdAccount {
  account_id: string;
  name: string;
  id: string;
}

interface MetaAdAccountsResponse {
  data?: MetaAdAccount[];
}

interface MetaInsightsRow {
  spend: string;
  impressions: string;
  clicks: string;
  conversions?: string;
  cpm: string;
  cpc: string;
  actions?: { action_type: string; value: string }[];
  purchase_roas?: { action_type: string; value: string }[];
  campaign_name?: string;
}

interface MetaInsightsResponse {
  data?: MetaInsightsRow[];
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
    .eq("provider", "meta_ads")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "Meta Ads not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "Meta Ads not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;
  const config = (integration.config || {}) as Record<string, string>;
  let adAccountId = config.meta_ads_account_id;

  if (!adAccountId) {
    // Fetch accessible ad accounts
    try {
      const pd = getPd();
      const res = await pd.proxy.get({
        url: "https://graph.facebook.com/v19.0/me/adaccounts?fields=account_id,name",
        accountId,
        externalUserId: brand_id,
      });

      const data = ((res as { data?: MetaAdAccountsResponse })?.data ?? res) as MetaAdAccountsResponse;
      const accounts = (data?.data || []).map((a) => ({
        account_id: a.account_id,
        name: a.name,
      }));

      return NextResponse.json({
        error: "No Meta Ads account configured",
        code: "NO_ACCOUNT_ID",
        accounts,
      });
    } catch {
      return NextResponse.json({ error: "No ad account configured" }, { status: 400 });
    }
  }

  // Normalize: ensure "act_" prefix
  if (!adAccountId.startsWith("act_")) {
    adAccountId = `act_${adAccountId}`;
  }

  try {
    const pd = getPd();

    const today = new Date();
    const startDate = new Date(today);
    startDate.setDate(startDate.getDate() - 28);
    const formatDate = (d: Date) => d.toISOString().split("T")[0];

    // Fetch account-level insights (28-day aggregate)
    const insightsRes = await pd.proxy.get({
      url: `https://graph.facebook.com/v19.0/${adAccountId}/insights?fields=spend,impressions,clicks,cpm,cpc,actions,purchase_roas&time_range={"since":"${formatDate(startDate)}","until":"${formatDate(today)}"}`,
      accountId,
      externalUserId: brand_id,
    });

    const insightsData = ((insightsRes as { data?: MetaInsightsResponse })?.data ?? insightsRes) as MetaInsightsResponse;
    const row = insightsData?.data?.[0];

    // Extract conversions from actions array
    const conversions = row?.actions?.find(
      (a) => a.action_type === "offsite_conversion.fb_pixel_purchase" || a.action_type === "purchase"
    );
    const roas = row?.purchase_roas?.[0];

    const overview = {
      spend: parseFloat(row?.spend || "0"),
      impressions: parseInt(row?.impressions || "0"),
      clicks: parseInt(row?.clicks || "0"),
      conversions: parseInt(conversions?.value || "0"),
      cpm: parseFloat(row?.cpm || "0"),
      cpc: parseFloat(row?.cpc || "0"),
      roas: parseFloat(roas?.value || "0"),
    };

    // Fetch per-campaign breakdown
    const campaignRes = await pd.proxy.get({
      url: `https://graph.facebook.com/v19.0/${adAccountId}/insights?fields=campaign_name,spend,impressions,clicks,actions&time_range={"since":"${formatDate(startDate)}","until":"${formatDate(today)}"}&level=campaign&sort=spend_descending&limit=10`,
      accountId,
      externalUserId: brand_id,
    });

    const campaignData = ((campaignRes as { data?: MetaInsightsResponse })?.data ?? campaignRes) as MetaInsightsResponse;
    const campaigns = (campaignData?.data || []).map((c) => {
      const conv = c.actions?.find(
        (a) => a.action_type === "offsite_conversion.fb_pixel_purchase" || a.action_type === "purchase"
      );
      return {
        name: c.campaign_name || "Unknown",
        spend: parseFloat(c.spend || "0"),
        impressions: parseInt(c.impressions || "0"),
        clicks: parseInt(c.clicks || "0"),
        conversions: parseInt(conv?.value || "0"),
      };
    });

    const snapshot = { ...overview, campaigns };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "paid_media",
      provider: "meta_ads",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Meta Ads sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
