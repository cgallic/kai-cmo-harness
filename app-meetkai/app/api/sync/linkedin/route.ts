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

interface LinkedInOrganization {
  id: number;
  localizedName: string;
}

interface LinkedInOrgAclElement {
  "organizationalTarget~"?: LinkedInOrganization;
  organizationalTarget?: string;
}

interface LinkedInOrgAclsResponse {
  elements?: LinkedInOrgAclElement[];
}

interface LinkedInOrgResponse {
  id?: number;
  localizedName?: string;
  followingInfo?: {
    followerCounts?: {
      organicFollowerCount?: number;
      paidFollowerCount?: number;
    };
  };
}

interface LinkedInShareStatElement {
  totalShareStatistics?: {
    impressionCount?: number;
    clickCount?: number;
    engagementRate?: number;
    shareCount?: number;
    uniqueImpressionsCount?: number;
  };
}

interface LinkedInShareStatsResponse {
  elements?: LinkedInShareStatElement[];
}

interface LinkedInFollowerStatElement {
  followerCounts?: {
    organicFollowerCount?: number;
    paidFollowerCount?: number;
  };
}

interface LinkedInFollowerStatsResponse {
  elements?: LinkedInFollowerStatElement[];
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
    .eq("provider", "linkedin")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "LinkedIn not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "LinkedIn not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;
  const config = (integration.config || {}) as Record<string, string>;
  const orgId = config.linkedin_organization_id;

  try {
    const pd = getPd();

    // If no organization selected, fetch available orgs and return for picker
    if (!orgId) {
      const orgsRes = await pd.proxy.get({
        url: "https://api.linkedin.com/v2/organizationAcls?q=roleAssignee&role=ADMINISTRATOR&projection=(elements*(organizationalTarget~(id,localizedName)))",
        accountId,
        externalUserId: brand_id,
      });

      const orgsData = ((orgsRes as { data?: LinkedInOrgAclsResponse })?.data ?? orgsRes) as LinkedInOrgAclsResponse;
      const organizations = (orgsData?.elements || [])
        .map((el) => {
          const org = el["organizationalTarget~"];
          if (!org) return null;
          return { id: String(org.id), name: org.localizedName };
        })
        .filter(Boolean);

      return NextResponse.json({
        error: "No LinkedIn Organization selected",
        code: "NO_ORG_SELECTED",
        organizations,
      });
    }

    // Fetch organization info for follower count
    const orgRes = await pd.proxy.get({
      url: `https://api.linkedin.com/v2/organizations/${orgId}`,
      accountId,
      externalUserId: brand_id,
    });

    const orgData = ((orgRes as { data?: LinkedInOrgResponse })?.data ?? orgRes) as LinkedInOrgResponse;
    const organizationName = orgData?.localizedName || "Unknown";

    // Fetch share statistics (impressions, clicks, engagement, shares)
    const shareStatsRes = await pd.proxy.get({
      url: `https://api.linkedin.com/v2/organizationalEntityShareStatistics?q=organizationalEntity&organizationalEntity=urn:li:organization:${orgId}`,
      accountId,
      externalUserId: brand_id,
    });

    const shareStatsData = ((shareStatsRes as { data?: LinkedInShareStatsResponse })?.data ?? shareStatsRes) as LinkedInShareStatsResponse;
    const shareStats = shareStatsData?.elements?.[0]?.totalShareStatistics;

    // Fetch follower statistics
    const followerStatsRes = await pd.proxy.get({
      url: `https://api.linkedin.com/v2/organizationalEntityFollowerStatistics?q=organizationalEntity&organizationalEntity=urn:li:organization:${orgId}`,
      accountId,
      externalUserId: brand_id,
    });

    const followerStatsData = ((followerStatsRes as { data?: LinkedInFollowerStatsResponse })?.data ?? followerStatsRes) as LinkedInFollowerStatsResponse;
    const followerCounts = followerStatsData?.elements?.[0]?.followerCounts;

    const totalFollowers =
      (followerCounts?.organicFollowerCount ?? 0) +
      (followerCounts?.paidFollowerCount ?? 0);

    const snapshot = {
      organization_name: organizationName,
      followers: totalFollowers,
      impressions: shareStats?.impressionCount ?? 0,
      clicks: shareStats?.clickCount ?? 0,
      engagement_rate: shareStats?.engagementRate ?? 0,
      shares: shareStats?.shareCount ?? 0,
      unique_impressions: shareStats?.uniqueImpressionsCount ?? 0,
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "social",
      provider: "linkedin",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("LinkedIn sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
