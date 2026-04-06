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

interface NotionSearchResponse {
  results?: { object: string }[];
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
    .eq("provider", "notion")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "Notion not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "Notion not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;

  try {
    const pd = getPd();

    // Notion search API requires POST — use proxy.post with filter for databases
    const dbRes = await pd.proxy.post({
      url: "https://api.notion.com/v1/search",
      accountId,
      externalUserId: brand_id,
      body: { filter: { property: "object", value: "database" } },
      headers: { "Notion-Version": "2022-06-28" },
    });

    const dbData = ((dbRes as { data?: NotionSearchResponse })?.data ?? dbRes) as NotionSearchResponse;

    // Search for pages
    const pageRes = await pd.proxy.post({
      url: "https://api.notion.com/v1/search",
      accountId,
      externalUserId: brand_id,
      body: { filter: { property: "object", value: "page" } },
      headers: { "Notion-Version": "2022-06-28" },
    });

    const pageData = ((pageRes as { data?: NotionSearchResponse })?.data ?? pageRes) as NotionSearchResponse;

    const snapshot = {
      databases_count: dbData?.results?.length ?? 0,
      pages_count: pageData?.results?.length ?? 0,
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "content",
      provider: "notion",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Notion sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
