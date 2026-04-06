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

interface FbPage {
  id: string;
  name: string;
  access_token: string;
}

interface FbPagesResponse {
  data?: FbPage[];
}

interface FbInsightValue {
  value: number;
}

interface FbInsight {
  name: string;
  values: FbInsightValue[];
}

interface FbInsightsResponse {
  data?: FbInsight[];
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
    .eq("provider", "facebook")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "Facebook not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "Facebook not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;
  const config = (integration.config || {}) as Record<string, string>;
  const selectedPageId = config.facebook_page_id;

  try {
    const pd = getPd();

    // Fetch user's pages
    const pagesRes = await pd.proxy.get({
      url: "https://graph.facebook.com/v19.0/me/accounts",
      accountId,
      externalUserId: brand_id,
    });

    const pagesData = ((pagesRes as { data?: FbPagesResponse })?.data ?? pagesRes) as FbPagesResponse;
    const pages = pagesData?.data || [];

    if (pages.length === 0) {
      return NextResponse.json({ error: "No Facebook Pages found", code: "NO_PAGES" }, { status: 404 });
    }

    // If no page selected, return available pages for picker
    if (!selectedPageId) {
      return NextResponse.json({
        error: "No Facebook Page selected",
        code: "NO_PAGE_SELECTED",
        pages: pages.map((p) => ({ id: p.id, name: p.name })),
      });
    }

    const page = pages.find((p) => p.id === selectedPageId);
    if (!page) {
      return NextResponse.json({ error: "Selected page not found", code: "PAGE_NOT_FOUND" }, { status: 404 });
    }

    // Fetch page insights (28-day period)
    const insightsRes = await pd.proxy.get({
      url: `https://graph.facebook.com/v19.0/${selectedPageId}/insights?metric=page_impressions,page_engaged_users,page_fans,page_views_total,page_actions_post_reactions_total&period=days_28`,
      accountId,
      externalUserId: brand_id,
    });

    const insightsData = ((insightsRes as { data?: FbInsightsResponse })?.data ?? insightsRes) as FbInsightsResponse;
    const insights = insightsData?.data || [];

    // Parse insights into a flat object
    const metricsMap: Record<string, number> = {};
    for (const insight of insights) {
      const val = insight.values?.[0]?.value ?? 0;
      metricsMap[insight.name] = val;
    }

    // Fetch recent posts count
    const postsRes = await pd.proxy.get({
      url: `https://graph.facebook.com/v19.0/${selectedPageId}/posts?limit=100&fields=id&since=${Math.floor(Date.now() / 1000) - 28 * 86400}`,
      accountId,
      externalUserId: brand_id,
    });

    const postsData = ((postsRes as { data?: { data?: { id: string }[] } })?.data ?? postsRes) as { data?: { id: string }[] };
    const postCount = postsData?.data?.length ?? 0;

    const snapshot = {
      page_name: page.name,
      page_id: selectedPageId,
      followers: metricsMap.page_fans ?? 0,
      impressions: metricsMap.page_impressions ?? 0,
      engaged_users: metricsMap.page_engaged_users ?? 0,
      page_views: metricsMap.page_views_total ?? 0,
      reactions: metricsMap.page_actions_post_reactions_total ?? 0,
      posts_28d: postCount,
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "social",
      provider: "facebook",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Facebook sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
