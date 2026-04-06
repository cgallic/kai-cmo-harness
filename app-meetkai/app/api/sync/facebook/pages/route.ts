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

interface FbPage {
  id: string;
  name: string;
}

interface FbPagesResponse {
  data?: FbPage[];
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
    .eq("provider", "facebook")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0 || !integrations[0].connected_account_id) {
    return NextResponse.json({ pages: [] });
  }

  const integration = integrations[0];

  try {
    const pd = getPd();
    const res = await pd.proxy.get({
      url: "https://graph.facebook.com/v19.0/me/accounts?fields=id,name",
      accountId: integration.connected_account_id,
      externalUserId: brandId,
    });

    const data = ((res as { data?: FbPagesResponse })?.data ?? res) as FbPagesResponse;
    const pages = (data?.data || []).map((p) => ({ id: p.id, name: p.name }));

    return NextResponse.json({ pages });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Facebook pages fetch error:", message);
    return NextResponse.json({ pages: [], error: message });
  }
}
