import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import { PipedreamClient } from "@pipedream/sdk";

export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { brand_id, provider } = await request.json();

  // Verify ownership
  const { data: brand } = await supabase
    .from("brands")
    .select("id")
    .eq("id", brand_id)
    .eq("user_id", user.id)
    .single();

  if (!brand) {
    return NextResponse.json({ error: "Brand not found" }, { status: 404 });
  }

  // Find the pending integration for this provider
  const { data: integration } = await supabase
    .from("integrations")
    .select("*")
    .eq("brand_id", brand_id)
    .eq("provider", provider)
    .eq("status", "pending_auth")
    .single();

  if (!integration) {
    return NextResponse.json({ error: "No pending integration found" }, { status: 404 });
  }

  // Look up the connected account from Pipedream
  let connectedAccountId: string | null = null;
  if (process.env.PIPEDREAM_CLIENT_ID && process.env.PIPEDREAM_CLIENT_SECRET) {
    try {
      const pd = new PipedreamClient({
        projectId: process.env.PIPEDREAM_PROJECT_ID!,
        projectEnvironment: (process.env.PIPEDREAM_ENVIRONMENT as "development" | "production") || "development",
        clientId: process.env.PIPEDREAM_CLIENT_ID!,
        clientSecret: process.env.PIPEDREAM_CLIENT_SECRET!,
      });

      const accountsPage = await pd.accounts.list({ externalUserId: brand_id });
      const accounts = accountsPage?.data ?? [];
      if (accounts.length > 0) {
        connectedAccountId = accounts[accounts.length - 1].id ?? null;
      }
    } catch (error) {
      console.error("Pipedream account lookup error:", error);
    }
  }

  // Mark integration as connected
  await supabase
    .from("integrations")
    .update({
      status: "connected",
      connected_account_id: connectedAccountId,
      connected_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
    .eq("id", integration.id);

  return NextResponse.json({ status: "connected", connected_account_id: connectedAccountId });
}
