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

interface ShopifyCountResponse {
  count?: number;
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
    .eq("provider", "shopify")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "Shopify not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "Shopify not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;
  const storeDomain = (integration.config as Record<string, string>)?.shopify_store;

  if (!storeDomain) {
    return NextResponse.json({ error: "Shopify store domain not configured. Set it in Connect settings.", code: "NO_CONFIG" }, { status: 400 });
  }

  // Normalize store domain
  const store = storeDomain.replace(/\.myshopify\.com$/, "").replace(/^https?:\/\//, "");

  try {
    const pd = getPd();

    // 30 days ago for orders
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();

    const [productsRes, ordersRes] = await Promise.all([
      pd.proxy.get({
        url: `https://${store}.myshopify.com/admin/api/2024-01/products/count.json`,
        accountId,
        externalUserId: brand_id,
      }),
      pd.proxy.get({
        url: `https://${store}.myshopify.com/admin/api/2024-01/orders/count.json?created_at_min=${thirtyDaysAgo}`,
        accountId,
        externalUserId: brand_id,
      }),
    ]);

    const productsData = ((productsRes as { data?: ShopifyCountResponse })?.data ?? productsRes) as ShopifyCountResponse;
    const ordersData = ((ordersRes as { data?: ShopifyCountResponse })?.data ?? ordersRes) as ShopifyCountResponse;

    const snapshot = {
      products_count: productsData?.count ?? 0,
      orders_count_30d: ordersData?.count ?? 0,
      store_domain: `${store}.myshopify.com`,
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "website",
      provider: "shopify",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Shopify sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
