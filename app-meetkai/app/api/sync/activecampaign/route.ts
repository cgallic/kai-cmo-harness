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

interface AcMetaResponse {
  meta?: { total?: string };
}

interface AcDeal {
  value?: string;
}

interface AcDealsResponse {
  deals?: AcDeal[];
  meta?: { total?: string };
}

interface AcAutomationsResponse {
  automations?: unknown[];
  meta?: { total?: string };
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
    .eq("provider", "activecampaign")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "ActiveCampaign not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "ActiveCampaign not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;

  try {
    const pd = getPd();

    // Pipedream resolves the account subdomain from the connected account
    const [contactsRes, campaignsRes, dealsRes, automationsRes] = await Promise.all([
      pd.proxy.get({
        url: "https://account.api-us1.com/api/3/contacts?limit=1",
        accountId,
        externalUserId: brand_id,
      }),
      pd.proxy.get({
        url: "https://account.api-us1.com/api/3/campaigns?limit=1",
        accountId,
        externalUserId: brand_id,
      }),
      pd.proxy.get({
        url: "https://account.api-us1.com/api/3/deals?limit=100",
        accountId,
        externalUserId: brand_id,
      }),
      pd.proxy.get({
        url: "https://account.api-us1.com/api/3/automations?limit=1",
        accountId,
        externalUserId: brand_id,
      }),
    ]);

    const contactsData = ((contactsRes as { data?: AcMetaResponse })?.data ?? contactsRes) as AcMetaResponse;
    const campaignsData = ((campaignsRes as { data?: AcMetaResponse })?.data ?? campaignsRes) as AcMetaResponse;
    const dealsData = ((dealsRes as { data?: AcDealsResponse })?.data ?? dealsRes) as AcDealsResponse;
    const automationsData = ((automationsRes as { data?: AcAutomationsResponse })?.data ?? automationsRes) as AcAutomationsResponse;

    const dealsValue = (dealsData?.deals || []).reduce(
      (sum, d) => sum + parseFloat(d.value || "0"), 0
    );

    const snapshot = {
      contacts_count: parseInt(contactsData?.meta?.total || "0"),
      campaigns_count: parseInt(campaignsData?.meta?.total || "0"),
      deals_count: parseInt(dealsData?.meta?.total || "0"),
      deals_value: Math.round(dealsValue * 100) / 100,
      automations_count: parseInt(automationsData?.meta?.total || "0"),
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "email",
      provider: "activecampaign",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("ActiveCampaign sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
