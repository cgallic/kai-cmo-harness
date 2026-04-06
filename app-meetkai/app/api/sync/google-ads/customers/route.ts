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

interface AccessibleCustomersResponse {
  resourceNames?: string[];
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
    .eq("provider", "google_ads")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0 || !integrations[0].connected_account_id) {
    return NextResponse.json({ customers: [] });
  }

  const integration = integrations[0];

  try {
    const pd = getPd();
    const accountId = integration.connected_account_id;
    console.log("Google Ads customers: fetching with accountId:", accountId, "brandId:", brandId);

    const res = await pd.proxy.get({
      url: "https://googleads.googleapis.com/v16/customers:listAccessibleCustomers",
      accountId,
      externalUserId: brandId,
    });

    const raw = res as Record<string, unknown>;
    const body = (raw.data ?? raw) as AccessibleCustomersResponse;
    console.log("Google Ads customers body:", JSON.stringify(body).substring(0, 500));

    const customers = (body?.resourceNames || []).map((rn) => {
      const id = rn.replace("customers/", "");
      return { id, name: id };
    });

    console.log("Google Ads customers found:", customers.length);
    return NextResponse.json({ customers });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Google Ads customers fetch error:", message);
    return NextResponse.json({ customers: [], error: message });
  }
}
