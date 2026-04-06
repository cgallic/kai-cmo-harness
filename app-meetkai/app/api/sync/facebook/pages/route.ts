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
    const accountId = integration.connected_account_id;
    console.log("Facebook pages: fetching with accountId:", accountId, "brandId:", brandId);

    const res = await pd.proxy.get({
      url: "https://graph.facebook.com/v19.0/me/accounts?fields=id,name",
      accountId,
      externalUserId: brandId,
    });

    // Pipedream SDK wraps response in { data: <body>, rawResponse: Response }
    const raw = res as Record<string, unknown>;
    console.log("Facebook pages raw response keys:", Object.keys(raw));
    const body = (raw.data ?? raw) as FbPagesResponse;
    console.log("Facebook pages body:", JSON.stringify(body).substring(0, 500));

    const pages = (body?.data || []).map((p) => ({ id: p.id, name: p.name }));

    console.log("Facebook pages found:", pages.length);
    return NextResponse.json({ pages });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Facebook pages fetch error:", message);
    return NextResponse.json({ pages: [], error: message });
  }
}
