import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import { PipedreamClient } from "@pipedream/sdk";

export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized", code: "UNAUTHORIZED" }, { status: 401 });
  }

  const { brand_id, provider } = await request.json();
  console.log("Confirming connection:", { brand_id, provider, user_id: user.id });

  // Verify ownership
  const { data: brand, error: brandError } = await supabase
    .from("brands")
    .select("id")
    .eq("id", brand_id)
    .eq("user_id", user.id)
    .single();

  if (!brand) {
    console.error("Brand not found:", brandError);
    return NextResponse.json({ error: "Brand not found", code: "BRAND_NOT_FOUND" }, { status: 404 });
  }

  // Use service role to bypass RLS for the update
  const serviceClient = await createServiceClient();

  // Find ANY integration for this brand+provider (not just pending_auth)
  const { data: integrations, error: findError } = await serviceClient
    .from("integrations")
    .select("*")
    .eq("brand_id", brand_id)
    .eq("provider", provider)
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    console.error("No integration found:", findError);
    return NextResponse.json({ error: "No integration found", code: "INTEGRATION_NOT_FOUND" }, { status: 404 });
  }

  const integration = integrations[0];
  console.log("Found integration:", integration.id, "status:", integration.status);

  // Look up the connected account from Pipedream
  let connectedAccountId: string | null = null;
  if (process.env.PIPEDREAM_CLIENT_ID && process.env.PIPEDREAM_CLIENT_SECRET) {
    try {
      const pd = new PipedreamClient({
        projectId: process.env.PIPEDREAM_PROJECT_ID!,
        projectEnvironment:
          (process.env.PIPEDREAM_ENVIRONMENT as
            | "development"
            | "production") || "development",
        clientId: process.env.PIPEDREAM_CLIENT_ID!,
        clientSecret: process.env.PIPEDREAM_CLIENT_SECRET!,
      });

      const accountsPage = await pd.accounts.list({
        externalUserId: brand_id,
      });
      const accounts = accountsPage?.data ?? [];
      if (accounts.length > 0) {
        connectedAccountId = accounts[accounts.length - 1].id ?? null;
      }
      console.log("Pipedream accounts found:", accounts.length, "using:", connectedAccountId);
    } catch (error) {
      console.error("Pipedream account lookup error:", error);
    }
  }

  // Mark integration as connected (service role bypasses RLS)
  const { error: updateError } = await serviceClient
    .from("integrations")
    .update({
      status: "connected",
      connected_account_id: connectedAccountId,
      connected_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
    .eq("id", integration.id);

  if (updateError) {
    console.error("Update failed:", updateError);
    return NextResponse.json({ error: "Failed to update integration", code: "UPDATE_FAILED" }, { status: 500 });
  }

  console.log("Integration confirmed as connected:", integration.id);
  return NextResponse.json({
    status: "connected",
    connected_account_id: connectedAccountId,
  });
}
