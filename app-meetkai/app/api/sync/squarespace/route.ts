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

interface SquarespaceProfile {
  id?: string;
  websiteTitle?: string;
  siteId?: string;
}

interface SquarespaceProfilesResponse {
  profiles?: SquarespaceProfile[];
}

interface SquarespaceOrder {
  id: string;
}

interface SquarespaceOrdersResponse {
  result?: SquarespaceOrder[];
  pagination?: { hasNextPage?: boolean; nextPageCursor?: string };
}

interface SquarespaceInventoryItem {
  id: string;
}

interface SquarespaceInventoryResponse {
  inventory?: SquarespaceInventoryItem[];
  pagination?: { hasNextPage?: boolean };
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
    .eq("provider", "squarespace")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "Squarespace not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "Squarespace not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;

  try {
    const pd = getPd();

    // Fetch site profiles
    let siteTitle = "Unknown";
    try {
      const profileRes = await pd.proxy.get({
        url: "https://api.squarespace.com/1.0/profiles",
        accountId,
        externalUserId: brand_id,
      });
      const profileData = ((profileRes as { data?: SquarespaceProfilesResponse })?.data ?? profileRes) as SquarespaceProfilesResponse;
      siteTitle = profileData?.profiles?.[0]?.websiteTitle || "Squarespace Site";
    } catch {
      // Profile endpoint may not be available on all plans
    }

    // Fetch recent orders (last 30 days)
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();
    let ordersCount = 0;
    try {
      const ordersRes = await pd.proxy.get({
        url: `https://api.squarespace.com/1.0/commerce/orders?modifiedAfter=${encodeURIComponent(thirtyDaysAgo)}`,
        accountId,
        externalUserId: brand_id,
      });
      const ordersData = ((ordersRes as { data?: SquarespaceOrdersResponse })?.data ?? ordersRes) as SquarespaceOrdersResponse;
      ordersCount = ordersData?.result?.length || 0;
    } catch {
      // Commerce API may not be available on non-commerce sites
    }

    // Fetch inventory / products
    let productsCount = 0;
    try {
      const inventoryRes = await pd.proxy.get({
        url: "https://api.squarespace.com/1.0/commerce/inventory",
        accountId,
        externalUserId: brand_id,
      });
      const inventoryData = ((inventoryRes as { data?: SquarespaceInventoryResponse })?.data ?? inventoryRes) as SquarespaceInventoryResponse;
      productsCount = inventoryData?.inventory?.length || 0;
    } catch {
      // Commerce API may not be available on non-commerce sites
    }

    const snapshot = {
      site_title: siteTitle,
      orders_count_30d: ordersCount,
      products_count: productsCount,
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "website",
      provider: "squarespace",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Squarespace sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
