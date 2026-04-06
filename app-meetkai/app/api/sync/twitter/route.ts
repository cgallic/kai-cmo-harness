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

interface TwitterUserResponse {
  data?: {
    username?: string;
    public_metrics?: {
      followers_count?: number;
      following_count?: number;
      tweet_count?: number;
      listed_count?: number;
    };
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
    .eq("provider", "twitter")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "X/Twitter not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "X/Twitter not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;

  try {
    const pd = getPd();

    const res = await pd.proxy.get({
      url: "https://api.twitter.com/2/users/me?user.fields=public_metrics",
      accountId,
      externalUserId: brand_id,
    });

    const data = ((res as { data?: TwitterUserResponse })?.data ?? res) as TwitterUserResponse;
    const metrics = data?.data?.public_metrics;

    const snapshot = {
      username: data?.data?.username ?? "",
      followers: metrics?.followers_count ?? 0,
      following: metrics?.following_count ?? 0,
      tweet_count: metrics?.tweet_count ?? 0,
      listed_count: metrics?.listed_count ?? 0,
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "social",
      provider: "twitter",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    // Gracefully handle 403 — Twitter API requires elevated access
    if (message.includes("403") || message.includes("Forbidden")) {
      return NextResponse.json({
        error: "Twitter API access requires an elevated developer account",
        code: "TWITTER_ACCESS_DENIED",
      }, { status: 403 });
    }
    console.error("Twitter sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
