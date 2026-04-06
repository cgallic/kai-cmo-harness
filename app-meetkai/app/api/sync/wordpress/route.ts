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
    .eq("provider", "wordpress")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "WordPress not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "WordPress not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;
  const siteUrl = (integration.config as Record<string, string>)?.wordpress_site_url;

  if (!siteUrl) {
    return NextResponse.json({ error: "WordPress site URL not configured. Set it in Connect settings.", code: "NO_CONFIG" }, { status: 400 });
  }

  // Normalize: strip trailing slash
  const baseUrl = siteUrl.replace(/\/+$/, "");

  try {
    const pd = getPd();

    const [postsRes, pagesRes] = await Promise.all([
      pd.proxy.get({
        url: `${baseUrl}/wp-json/wp/v2/posts?per_page=1&_fields=id`,
        accountId,
        externalUserId: brand_id,
      }),
      pd.proxy.get({
        url: `${baseUrl}/wp-json/wp/v2/pages?per_page=1&_fields=id`,
        accountId,
        externalUserId: brand_id,
      }),
    ]);

    // WP REST API returns total count in x-wp-total header.
    // Via Pipedream proxy we may not get headers, so fall back to array check.
    const postsData = ((postsRes as { data?: unknown })?.data ?? postsRes) as unknown;
    const pagesData = ((pagesRes as { data?: unknown })?.data ?? pagesRes) as unknown;

    // If we got headers with totals, use them; otherwise use array length as minimum
    const postsHeaders = (postsRes as { headers?: Record<string, string> })?.headers;
    const pagesHeaders = (pagesRes as { headers?: Record<string, string> })?.headers;

    const postsCount = postsHeaders?.["x-wp-total"]
      ? parseInt(postsHeaders["x-wp-total"])
      : Array.isArray(postsData) ? postsData.length : 0;

    const pagesCount = pagesHeaders?.["x-wp-total"]
      ? parseInt(pagesHeaders["x-wp-total"])
      : Array.isArray(pagesData) ? pagesData.length : 0;

    const snapshot = {
      posts_count: postsCount,
      pages_count: pagesCount,
      site_url: baseUrl,
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "website",
      provider: "wordpress",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("WordPress sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
