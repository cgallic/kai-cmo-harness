import { createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

interface PipedreamWebhookPayload {
  id: string; // connected account id
  external_user_id: string; // brand_id we passed when creating the token
  app?: {
    name_slug?: string;
  };
  [key: string]: unknown;
}

// POST /api/connections/webhook
// Called by Pipedream when OAuth completes — no user session, use service role.
// This is the server-side confirmation path: reliable even if the popup/browser
// is closed before the client-side confirm fires.
export async function POST(request: Request) {
  const body = (await request.json()) as PipedreamWebhookPayload;

  // Pipedream sends: { id, external_user_id, app: { name_slug }, ... }
  const { external_user_id: brandId, id: accountId, app } = body;

  if (!brandId || !accountId) {
    return NextResponse.json(
      { error: "Missing required fields: id and external_user_id", code: "MISSING_FIELDS" },
      { status: 400 },
    );
  }

  const serviceClient = await createServiceClient();

  // Find the most recent pending integration for this brand
  const { data: integration } = await serviceClient
    .from("integrations")
    .select("*")
    .eq("brand_id", brandId)
    .eq("status", "pending_auth")
    .order("created_at", { ascending: false })
    .limit(1)
    .single();

  if (integration) {
    await serviceClient
      .from("integrations")
      .update({
        status: "connected",
        connected_account_id: accountId,
        connected_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
      .eq("id", integration.id);

    console.log(
      `[webhook] Integration ${integration.id} confirmed for brand ${brandId}` +
        (app?.name_slug ? ` (app: ${app.name_slug})` : ""),
    );
  } else {
    // No pending integration found — the client-side confirm may have already
    // processed this, or the brand_id is stale. Log but don't fail.
    console.warn(
      `[webhook] No pending integration found for brand ${brandId}`,
    );
  }

  return NextResponse.json({ ok: true });
}
