import { createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

// Pipedream sends this webhook when OAuth completes
export async function POST(request: Request) {
  const body = await request.json();

  // Pipedream connect webhook payload
  const { external_user_id, account_id, app } = body;

  if (!external_user_id || !account_id) {
    return NextResponse.json({ error: "Missing required fields", code: "MISSING_FIELDS" }, { status: 400 });
  }

  const supabase = await createServiceClient();

  // Find the pending integration for this brand + app
  const { data: integrations } = await supabase
    .from("integrations")
    .select("*")
    .eq("brand_id", external_user_id)
    .eq("status", "pending_auth");

  if (integrations && integrations.length > 0) {
    // Update the first matching pending integration
    const integration = integrations[0];
    await supabase
      .from("integrations")
      .update({
        status: "connected",
        connected_account_id: account_id,
        connected_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
      .eq("id", integration.id);
  }

  return NextResponse.json({ ok: true });
}
