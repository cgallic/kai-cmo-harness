import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";
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

interface GscSiteEntry {
  siteUrl: string;
  permissionLevel: string;
}

interface GscSitesResponse {
  siteEntry?: GscSiteEntry[];
}

export interface GscSite {
  site_url: string;
  permission_level: string;
}

export async function GET(request: NextRequest) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const brandId = request.nextUrl.searchParams.get("brand_id");
  if (!brandId) {
    return NextResponse.json({ error: "brand_id is required" }, { status: 400 });
  }

  // Verify brand ownership
  const { data: brand, error: brandErr } = await supabase
    .from("brands")
    .select("id")
    .eq("id", brandId)
    .eq("user_id", user.id)
    .single();

  if (brandErr || !brand) {
    return NextResponse.json({ error: "Brand not found", code: "BRAND_NOT_FOUND" }, { status: 404 });
  }

  const serviceClient = await createServiceClient();

  // Support optional integration_id param to target a specific connection
  const integrationId = request.nextUrl.searchParams.get("integration_id");

  let integration: Record<string, unknown> | null = null;

  if (integrationId) {
    const { data, error } = await serviceClient
      .from("integrations")
      .select("*")
      .eq("id", integrationId)
      .eq("brand_id", brandId)
      .eq("provider", "google_search_console")
      .eq("status", "connected")
      .single();
    if (!error && data) integration = data as Record<string, unknown>;
  } else {
    // Use .limit(1) to gracefully handle multiple GSC integrations
    const { data: rows } = await serviceClient
      .from("integrations")
      .select("*")
      .eq("brand_id", brandId)
      .eq("provider", "google_search_console")
      .eq("status", "connected")
      .order("created_at", { ascending: false })
      .limit(1);
    if (rows && rows.length > 0) integration = rows[0] as Record<string, unknown>;
  }

  if (!integration?.connected_account_id) {
    return NextResponse.json(
      { error: "Google Search Console not connected", code: "GSC_NOT_CONNECTED" },
      { status: 404 }
    );
  }

  try {
    const pd = getPd();
    const res = await pd.proxy.get({
      url: "https://www.googleapis.com/webmasters/v3/sites",
      accountId: integration.connected_account_id as string,
      externalUserId: brandId,
    });

    const data = ((res as { data?: GscSitesResponse })?.data ??
      res) as GscSitesResponse;

    const sites: GscSite[] = (data?.siteEntry || []).map((entry) => ({
      site_url: entry.siteUrl,
      permission_level: entry.permissionLevel,
    }));

    return NextResponse.json({ sites });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("GSC sites error:", message);
    return NextResponse.json(
      { error: "Failed to fetch sites", code: "FETCH_SITES_FAILED", detail: message },
      { status: 500 }
    );
  }
}
