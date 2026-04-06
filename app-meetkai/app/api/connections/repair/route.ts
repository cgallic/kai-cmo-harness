import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import { PipedreamClient } from "@pipedream/sdk";
import { PROVIDERS } from "@/lib/types";

/**
 * POST /api/connections/repair
 * Re-matches all connected integrations with their correct Pipedream account IDs.
 * Fixes the case where confirm grabbed the wrong account.
 */
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

  // Get all connected integrations for this brand
  const { data: integrations } = await serviceClient
    .from("integrations")
    .select("*")
    .eq("brand_id", brand_id)
    .eq("status", "connected");

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ message: "No connected integrations", repairs: [] });
  }

  const pd = new PipedreamClient({
    projectId: process.env.PIPEDREAM_PROJECT_ID!,
    projectEnvironment:
      (process.env.PIPEDREAM_ENVIRONMENT as "development" | "production") || "development",
    clientId: process.env.PIPEDREAM_CLIENT_ID!,
    clientSecret: process.env.PIPEDREAM_CLIENT_SECRET!,
  });

  // List ALL Pipedream accounts for this brand
  const allAccountsPage = await pd.accounts.list({ externalUserId: brand_id });
  const allAccounts = allAccountsPage?.data ?? [];

  console.log("Repair: All Pipedream accounts for brand:", allAccounts.map((a) => ({
    id: a.id,
    app: a.app,
    healthy: a.healthy,
    dead: a.dead,
  })));

  const repairs: { provider: string; old_account_id: string | null; new_account_id: string | null; matched_app: string }[] = [];

  for (const integration of integrations) {
    const providerConfig = PROVIDERS.find((p) => p.provider === integration.provider);
    if (!providerConfig?.appSlug) continue;

    // Find the Pipedream account that matches this provider's app slug
    const matchingAccount = allAccounts.find((a) => {
      const appSlug = a.app?.nameSlug || a.app?.id || "";
      return appSlug === providerConfig.appSlug;
    });

    if (matchingAccount && matchingAccount.id !== integration.connected_account_id) {
      // Fix mismatched account
      await serviceClient
        .from("integrations")
        .update({
          connected_account_id: matchingAccount.id,
          updated_at: new Date().toISOString(),
        })
        .eq("id", integration.id);

      repairs.push({
        provider: integration.provider,
        old_account_id: integration.connected_account_id,
        new_account_id: matchingAccount.id ?? null,
        matched_app: providerConfig.appSlug,
      });

      console.log(`Repair: ${integration.provider} ${integration.connected_account_id} → ${matchingAccount.id}`);
    }
  }

  return NextResponse.json({
    message: `Repaired ${repairs.length} of ${integrations.length} integrations`,
    total_pipedream_accounts: allAccounts.length,
    accounts: allAccounts.map((a) => ({
      id: a.id,
      app: a.app,
      healthy: a.healthy,
    })),
    repairs,
  });
}
