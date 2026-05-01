import { createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import crypto from "crypto";
import { z } from "zod";

const pipedreamWebhookSchema = z.object({
  id: z.string().min(1),
  external_user_id: z.string().min(1),
  app: z.object({ name_slug: z.string().optional() }).optional(),
}).passthrough();

function verifyPipedreamSignature(rawBody: string, request: Request): boolean {
  const secret = process.env.PIPEDREAM_WEBHOOK_SECRET;
  if (!secret) return true;

  const header =
    request.headers.get("x-pipedream-signature") ||
    request.headers.get("x-pd-signature") ||
    request.headers.get("x-signature");

  if (!header) return false;

  const expected = crypto
    .createHmac("sha256", secret)
    .update(rawBody, "utf8")
    .digest("hex");
  const provided = header.replace(/^sha256=/i, "").trim();

  try {
    return crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(provided));
  } catch {
    return false;
  }
}

// POST /api/connections/webhook
// Called by Pipedream when OAuth completes — no user session, use service role.
// This is the server-side confirmation path: reliable even if the popup/browser
// is closed before the client-side confirm fires.
export async function POST(request: Request) {
  const rawBody = await request.text();
  if (!verifyPipedreamSignature(rawBody, request)) {
    return NextResponse.json(
      { error: "Invalid webhook signature", code: "INVALID_SIGNATURE" },
      { status: 401 },
    );
  }

  let json: unknown;
  try {
    json = JSON.parse(rawBody);
  } catch {
    return NextResponse.json(
      { error: "Invalid JSON body", code: "INVALID_JSON" },
      { status: 400 },
    );
  }

  const parsed = pipedreamWebhookSchema.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "Invalid webhook body", code: "INVALID_BODY", issues: parsed.error.issues },
      { status: 400 },
    );
  }

  const body = parsed.data;

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
  const { data: integrations } = await serviceClient
    .from("integrations")
    .select("*")
    .eq("brand_id", brandId)
    .eq("status", "pending_auth")
    .order("created_at", { ascending: false })
    .limit(1);

  const integration = integrations?.[0] ?? null;

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
