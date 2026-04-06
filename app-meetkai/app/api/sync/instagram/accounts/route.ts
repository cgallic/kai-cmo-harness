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
  instagram_business_account?: { id: string };
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
    .eq("provider", "instagram")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0 || !integrations[0].connected_account_id) {
    return NextResponse.json({ accounts: [] });
  }

  const integration = integrations[0];

  try {
    const pd = getPd();

    // Fetch Facebook Pages with linked Instagram Business accounts
    const res = await pd.proxy.get({
      url: "https://graph.facebook.com/v19.0/me/accounts?fields=id,name,instagram_business_account",
      accountId: integration.connected_account_id,
      externalUserId: brandId,
    });

    const data = ((res as { data?: FbPagesResponse })?.data ?? res) as FbPagesResponse;
    const pages = (data?.data || []).filter((p) => p.instagram_business_account?.id);

    // Fetch username for each IG account
    const accounts = await Promise.all(
      pages.map(async (p) => {
        const igId = p.instagram_business_account!.id;
        try {
          const profileRes = await pd.proxy.get({
            url: `https://graph.facebook.com/v19.0/${igId}?fields=username`,
            accountId: integration.connected_account_id,
            externalUserId: brandId,
          });
          const profile = ((profileRes as { data?: { username?: string } })?.data ?? profileRes) as { username?: string };
          return { id: igId, name: p.name, username: profile.username || p.name };
        } catch {
          return { id: igId, name: p.name, username: p.name };
        }
      })
    );

    return NextResponse.json({ accounts });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Instagram accounts fetch error:", message);
    return NextResponse.json({ accounts: [], error: message });
  }
}
