import { createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

const SYNC_ENDPOINTS: Record<string, string> = {
  ga4: "/api/analytics/sync",
  gsc: "/api/analytics/sync-gsc",
  facebook: "/api/sync/facebook",
  instagram: "/api/sync/instagram",
  linkedin: "/api/sync/linkedin",
  youtube: "/api/sync/youtube",
  pinterest: "/api/sync/pinterest",
  google_ads: "/api/sync/google-ads",
  meta_ads: "/api/sync/meta-ads",
  mailchimp: "/api/sync/mailchimp",
  sendgrid: "/api/sync/sendgrid",
  klaviyo: "/api/sync/klaviyo",
  hubspot: "/api/sync/hubspot",
  stripe: "/api/sync/stripe",
  convertkit: "/api/sync/convertkit",
  activecampaign: "/api/sync/activecampaign",
  twitter: "/api/sync/twitter",
  calendly: "/api/sync/calendly",
  notion: "/api/sync/notion",
  google_sheets: "/api/sync/google-sheets",
  airtable: "/api/sync/airtable",
  wordpress: "/api/sync/wordpress",
  shopify: "/api/sync/shopify",
  webflow: "/api/sync/webflow",
  squarespace: "/api/sync/squarespace",
  slack: "/api/sync/slack",
  gbp: "/api/sync/gbp",
};

export async function GET(request: Request) {
  // Verify cron secret
  const authHeader = request.headers.get("authorization");
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const serviceClient = await createServiceClient();

  // Fetch all connected integrations
  const { data: integrations, error } = await serviceClient
    .from("integrations")
    .select("brand_id, provider")
    .eq("status", "connected");

  if (error || !integrations) {
    return NextResponse.json({ error: "Failed to fetch integrations" }, { status: 500 });
  }

  // Group by brand_id
  const brandProviders = new Map<string, string[]>();
  for (const { brand_id, provider } of integrations) {
    const providers = brandProviders.get(brand_id) || [];
    providers.push(provider);
    brandProviders.set(brand_id, providers);
  }

  const results: { brand_id: string; provider: string; status: string }[] = [];
  const baseUrl = process.env.VERCEL_URL
    ? `https://${process.env.VERCEL_URL}`
    : "http://localhost:3000";

  for (const [brand_id, providers] of Array.from(brandProviders.entries())) {
    for (const provider of providers) {
      const endpoint = SYNC_ENDPOINTS[provider];
      if (!endpoint) continue;

      try {
        const res = await fetch(`${baseUrl}${endpoint}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ brand_id }),
        });

        results.push({
          brand_id,
          provider,
          status: res.ok ? "synced" : `error:${res.status}`,
        });
      } catch (err) {
        results.push({
          brand_id,
          provider,
          status: `error:${err instanceof Error ? err.message : "unknown"}`,
        });
      }
    }
  }

  const synced = results.filter((r) => r.status === "synced").length;
  const failed = results.length - synced;

  console.log(`Cron sync-all: ${synced} synced, ${failed} failed out of ${results.length} total`);

  return NextResponse.json({
    status: "completed",
    summary: { total: results.length, synced, failed },
    results,
  });
}
