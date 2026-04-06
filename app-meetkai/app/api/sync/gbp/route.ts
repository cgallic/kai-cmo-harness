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

interface GbpAccount {
  name: string;
  accountName?: string;
  type?: string;
}

interface GbpAccountsResponse {
  accounts?: GbpAccount[];
}

interface GbpLocation {
  name: string;
  title?: string;
  storefrontAddress?: {
    addressLines?: string[];
    locality?: string;
    administrativeArea?: string;
  };
  websiteUri?: string;
  phoneNumbers?: { primaryPhone?: string };
}

interface GbpLocationsResponse {
  locations?: GbpLocation[];
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
    .eq("provider", "gbp")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "Google Business not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "Google Business not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;

  try {
    const pd = getPd();

    // List GBP accounts
    const accountsRes = await pd.proxy.get({
      url: "https://mybusinessaccountmanagement.googleapis.com/v1/accounts",
      accountId,
      externalUserId: brand_id,
    });
    const accountsData = ((accountsRes as { data?: GbpAccountsResponse })?.data ?? accountsRes) as GbpAccountsResponse;
    const accounts = accountsData?.accounts || [];

    // For each account, list locations
    const allLocations: { name: string; title: string; address: string; website: string | null; phone: string | null }[] = [];

    for (const account of accounts.slice(0, 5)) {
      try {
        const locRes = await pd.proxy.get({
          url: `https://mybusinessbusinessinformation.googleapis.com/v1/${account.name}/locations?readMask=name,title,storefrontAddress,websiteUri,phoneNumbers`,
          accountId,
          externalUserId: brand_id,
        });
        const locData = ((locRes as { data?: GbpLocationsResponse })?.data ?? locRes) as GbpLocationsResponse;
        const locations = locData?.locations || [];

        for (const loc of locations) {
          const addrParts = [
            ...(loc.storefrontAddress?.addressLines || []),
            loc.storefrontAddress?.locality,
            loc.storefrontAddress?.administrativeArea,
          ].filter(Boolean);

          allLocations.push({
            name: loc.name,
            title: loc.title || "Unnamed",
            address: addrParts.join(", "),
            website: loc.websiteUri || null,
            phone: loc.phoneNumbers?.primaryPhone || null,
          });
        }
      } catch {
        // Some accounts may not have location access
      }
    }

    const snapshot = {
      accounts_count: accounts.length,
      locations_count: allLocations.length,
      locations: allLocations.slice(0, 20),
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "analytics",
      provider: "gbp",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("GBP sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
