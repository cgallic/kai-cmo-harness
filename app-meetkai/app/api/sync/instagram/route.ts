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
  instagram_business_account?: { id: string };
}

interface FbPagesResponse {
  data?: FbPage[];
}

interface IgProfile {
  followers_count: number;
  media_count: number;
  username: string;
}

interface IgInsightValue {
  value: number;
}

interface IgInsight {
  name: string;
  values: IgInsightValue[];
}

interface IgInsightsResponse {
  data?: IgInsight[];
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
    .eq("provider", "instagram")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "Instagram not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "Instagram not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;
  const config = (integration.config || {}) as Record<string, string>;
  const selectedIgAccountId = config.instagram_account_id;

  try {
    const pd = getPd();

    // Fetch user's Facebook Pages to find linked Instagram Business accounts
    const pagesRes = await pd.proxy.get({
      url: "https://graph.facebook.com/v19.0/me/accounts?fields=id,name,instagram_business_account",
      accountId,
      externalUserId: brand_id,
    });

    const pagesData = ((pagesRes as { data?: FbPagesResponse })?.data ?? pagesRes) as FbPagesResponse;
    const pages = pagesData?.data || [];

    // Filter to only pages with an Instagram Business account
    const pagesWithIg = pages.filter((p) => p.instagram_business_account?.id);

    if (pagesWithIg.length === 0) {
      return NextResponse.json({
        error: "No Instagram Business accounts found",
        code: "NO_IG_ACCOUNTS",
      }, { status: 404 });
    }

    // If no IG account selected, return available accounts for picker
    if (!selectedIgAccountId) {
      // Fetch usernames for each IG account
      const accounts = await Promise.all(
        pagesWithIg.map(async (p) => {
          const igId = p.instagram_business_account!.id;
          try {
            const profileRes = await pd.proxy.get({
              url: `https://graph.facebook.com/v19.0/${igId}?fields=username`,
              accountId,
              externalUserId: brand_id,
            });
            const profile = ((profileRes as { data?: { username?: string } })?.data ?? profileRes) as { username?: string };
            return { id: igId, name: p.name, username: profile.username || p.name };
          } catch {
            return { id: igId, name: p.name, username: p.name };
          }
        })
      );

      return NextResponse.json({
        error: "No Instagram account selected",
        code: "NO_ACCOUNT_SELECTED",
        accounts,
      });
    }

    // Verify the selected IG account is still accessible
    const matchedPage = pagesWithIg.find(
      (p) => p.instagram_business_account?.id === selectedIgAccountId
    );
    if (!matchedPage) {
      return NextResponse.json({
        error: "Selected Instagram account not found",
        code: "ACCOUNT_NOT_FOUND",
      }, { status: 404 });
    }

    const igId = selectedIgAccountId;

    // Fetch IG profile info
    const profileRes = await pd.proxy.get({
      url: `https://graph.facebook.com/v19.0/${igId}?fields=followers_count,media_count,username`,
      accountId,
      externalUserId: brand_id,
    });

    const profile = ((profileRes as { data?: IgProfile })?.data ?? profileRes) as IgProfile;

    // Fetch IG insights (28-day window)
    const insightsRes = await pd.proxy.get({
      url: `https://graph.facebook.com/v19.0/${igId}/insights?metric=impressions,reach,profile_views,website_clicks&period=days_28`,
      accountId,
      externalUserId: brand_id,
    });

    const insightsData = ((insightsRes as { data?: IgInsightsResponse })?.data ?? insightsRes) as IgInsightsResponse;
    const insights = insightsData?.data || [];

    // Parse insights into a flat object
    const metricsMap: Record<string, number> = {};
    for (const insight of insights) {
      const val = insight.values?.[0]?.value ?? 0;
      metricsMap[insight.name] = val;
    }

    const snapshot = {
      username: profile.username || "unknown",
      followers: profile.followers_count ?? 0,
      media_count: profile.media_count ?? 0,
      impressions: metricsMap.impressions ?? 0,
      reach: metricsMap.reach ?? 0,
      profile_views: metricsMap.profile_views ?? 0,
      website_clicks: metricsMap.website_clicks ?? 0,
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "social",
      provider: "instagram",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Instagram sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
