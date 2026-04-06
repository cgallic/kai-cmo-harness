import { createServiceClient } from "@/lib/supabase/server";
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

interface MetaAdAccount {
  account_id: string;
  name: string;
  id: string;
}

interface MetaAdAccountsResponse {
  data?: MetaAdAccount[];
}

export async function GET(request: NextRequest) {
  const brandId = request.nextUrl.searchParams.get("brand_id");
  if (!brandId) {
    return NextResponse.json({ error: "brand_id required" }, { status: 400 });
  }

  const serviceClient = await createServiceClient();

  const { data: integrations } = await serviceClient
    .from("integrations")
    .select("*")
    .eq("brand_id", brandId)
    .eq("provider", "meta_ads")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0 || !integrations[0].connected_account_id) {
    return NextResponse.json({ accounts: [] });
  }

  const integration = integrations[0];

  try {
    const pd = getPd();
    const accountId = integration.connected_account_id;
    console.log("Meta Ads accounts: fetching with accountId:", accountId, "brandId:", brandId);

    const res = await pd.proxy.get({
      url: "https://graph.facebook.com/v19.0/me/adaccounts?fields=account_id,name",
      accountId,
      externalUserId: brandId,
    });

    const raw = res as Record<string, unknown>;
    const body = (raw.data ?? raw) as MetaAdAccountsResponse;
    console.log("Meta Ads accounts body:", JSON.stringify(body).substring(0, 500));

    const accounts = (body?.data || []).map((a) => ({
      id: a.account_id,
      name: a.name || `Account ${a.account_id}`,
    }));

    console.log("Meta Ads accounts found:", accounts.length);
    return NextResponse.json({ accounts });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Meta Ads accounts fetch error:", message);
    return NextResponse.json({ accounts: [], error: message });
  }
}
