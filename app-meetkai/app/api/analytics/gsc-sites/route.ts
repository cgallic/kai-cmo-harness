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
  const { data: brand } = await supabase
    .from("brands")
    .select("id")
    .eq("id", brandId)
    .eq("user_id", user.id)
    .single();

  if (!brand) {
    return NextResponse.json({ error: "Brand not found" }, { status: 404 });
  }

  const serviceClient = await createServiceClient();

  const { data: integration } = await serviceClient
    .from("integrations")
    .select("*")
    .eq("brand_id", brandId)
    .eq("provider", "google_search_console")
    .eq("status", "connected")
    .single();

  if (!integration?.connected_account_id) {
    return NextResponse.json(
      { error: "Google Search Console not connected" },
      { status: 404 }
    );
  }

  try {
    const pd = getPd();
    const res = await pd.proxy.get({
      url: "https://www.googleapis.com/webmasters/v3/sites",
      accountId: integration.connected_account_id,
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
      { error: "Failed to fetch sites", detail: message },
      { status: 502 }
    );
  }
}
