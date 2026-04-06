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

interface KlaviyoListAttributes {
  name: string;
}

interface KlaviyoList {
  id: string;
  attributes: KlaviyoListAttributes;
}

interface KlaviyoListsResponse {
  data?: KlaviyoList[];
}

interface KlaviyoCampaignAttributes {
  name: string;
  status: string;
}

interface KlaviyoCampaign {
  id: string;
  attributes: KlaviyoCampaignAttributes;
}

interface KlaviyoCampaignsResponse {
  data?: KlaviyoCampaign[];
}

interface KlaviyoProfileCountResponse {
  data?: { attributes?: { profile_count?: number } };
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
    .eq("provider", "klaviyo")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "Klaviyo not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "Klaviyo not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;
  const klaviyoHeaders = { revision: "2024-02-15" };

  try {
    const pd = getPd();

    // Fetch all lists
    const listsRes = await pd.proxy.get({
      url: "https://a.klaviyo.com/api/lists/",
      accountId,
      externalUserId: brand_id,
      headers: klaviyoHeaders,
    });

    const listsData = ((listsRes as { data?: KlaviyoListsResponse })?.data ?? listsRes) as KlaviyoListsResponse;
    const rawLists = listsData?.data || [];

    // Fetch profile counts for each list
    const lists = await Promise.all(
      rawLists.map(async (list) => {
        try {
          const countRes = await pd.proxy.get({
            url: `https://a.klaviyo.com/api/lists/${list.id}/profiles/?page[size]=1`,
            accountId,
            externalUserId: brand_id,
            headers: klaviyoHeaders,
          });

          // Klaviyo returns total count in meta or we can use the list relationships endpoint
          // For the profiles count, use the tags endpoint pattern
          const countData = ((countRes as { data?: KlaviyoProfileCountResponse })?.data ?? countRes) as KlaviyoProfileCountResponse;
          const profileCount = countData?.data?.attributes?.profile_count ?? 0;

          return {
            id: list.id,
            name: list.attributes.name,
            profile_count: profileCount,
          };
        } catch {
          return {
            id: list.id,
            name: list.attributes.name,
            profile_count: 0,
          };
        }
      })
    );

    const totalSubscribers = lists.reduce((sum, l) => sum + l.profile_count, 0);

    // Fetch recent email campaigns
    const campaignsRes = await pd.proxy.get({
      url: "https://a.klaviyo.com/api/campaigns/?filter=equals(messages.channel,'email')&sort=-scheduled_at&page[size]=10",
      accountId,
      externalUserId: brand_id,
      headers: klaviyoHeaders,
    });

    const campaignsData = ((campaignsRes as { data?: KlaviyoCampaignsResponse })?.data ?? campaignsRes) as KlaviyoCampaignsResponse;
    const rawCampaigns = campaignsData?.data || [];

    const recentCampaigns = rawCampaigns.map((c) => ({
      id: c.id,
      name: c.attributes.name,
      status: c.attributes.status,
    }));

    const snapshot = {
      list_count: lists.length,
      total_subscribers: totalSubscribers,
      lists,
      recent_campaigns: recentCampaigns,
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "email",
      provider: "klaviyo",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Klaviyo sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
