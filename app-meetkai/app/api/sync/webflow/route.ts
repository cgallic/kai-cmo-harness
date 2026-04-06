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

interface WebflowSite {
  id: string;
  displayName?: string;
  shortName?: string;
  lastPublished?: string;
  customDomains?: { url: string }[];
}

interface WebflowSitesResponse {
  sites?: WebflowSite[];
}

interface WebflowPage {
  id: string;
  title?: string;
}

interface WebflowPagesResponse {
  pages?: WebflowPage[];
}

interface WebflowCollection {
  id: string;
  displayName?: string;
}

interface WebflowCollectionsResponse {
  collections?: WebflowCollection[];
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
    .eq("provider", "webflow")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "Webflow not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "Webflow not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;

  try {
    const pd = getPd();

    // List all sites
    const sitesRes = await pd.proxy.get({
      url: "https://api.webflow.com/v2/sites",
      accountId,
      externalUserId: brand_id,
    });
    const sitesData = ((sitesRes as { data?: WebflowSitesResponse })?.data ?? sitesRes) as WebflowSitesResponse;
    const sites = sitesData?.sites || [];

    let totalPages = 0;
    let totalCollections = 0;

    // For each site, fetch pages and collections counts
    for (const site of sites.slice(0, 5)) {
      const [pagesRes, collectionsRes] = await Promise.all([
        pd.proxy.get({
          url: `https://api.webflow.com/v2/sites/${site.id}/pages`,
          accountId,
          externalUserId: brand_id,
        }),
        pd.proxy.get({
          url: `https://api.webflow.com/v2/sites/${site.id}/collections`,
          accountId,
          externalUserId: brand_id,
        }),
      ]);

      const pagesData = ((pagesRes as { data?: WebflowPagesResponse })?.data ?? pagesRes) as WebflowPagesResponse;
      const collectionsData = ((collectionsRes as { data?: WebflowCollectionsResponse })?.data ?? collectionsRes) as WebflowCollectionsResponse;

      totalPages += pagesData?.pages?.length || 0;
      totalCollections += collectionsData?.collections?.length || 0;
    }

    const snapshot = {
      sites_count: sites.length,
      total_pages: totalPages,
      total_collections: totalCollections,
      sites: sites.slice(0, 10).map((s) => ({
        id: s.id,
        name: s.displayName || s.shortName || s.id,
        last_published: s.lastPublished || null,
        domain: s.customDomains?.[0]?.url || null,
      })),
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "website",
      provider: "webflow",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Webflow sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
