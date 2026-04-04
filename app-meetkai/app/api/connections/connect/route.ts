import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

export async function POST(request: Request) {
  // Verify authenticated user
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await request.json();
  const { brand_id, channel, provider, app_slug } = body;

  // Verify user owns this brand
  const { data: brand } = await supabase
    .from("brands")
    .select("id")
    .eq("id", brand_id)
    .eq("user_id", user.id)
    .single();

  if (!brand) {
    return NextResponse.json({ error: "Brand not found" }, { status: 404 });
  }

  // Create or update integration record
  const { data: existing } = await supabase
    .from("integrations")
    .select("id")
    .eq("brand_id", brand_id)
    .eq("channel", channel)
    .eq("provider", provider)
    .single();

  if (existing) {
    await supabase
      .from("integrations")
      .update({ status: "pending_auth", updated_at: new Date().toISOString() })
      .eq("id", existing.id);
  } else {
    await supabase.from("integrations").insert({
      brand_id,
      channel,
      provider,
      status: "pending_auth",
    });
  }

  // If Pipedream keys are configured, create a real connect token
  const pipedreamSecret = process.env.PIPEDREAM_CLIENT_SECRET;
  if (pipedreamSecret) {
    try {
      const tokenRes = await fetch(
        "https://api.pipedream.com/v1/connect/tokens",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${pipedreamSecret}`,
          },
          body: JSON.stringify({
            external_user_id: brand_id,
            ...(app_slug ? { app: app_slug } : {}),
            allowed_origins: [
              process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3010",
            ],
            success_redirect_uri: `${process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3010"}/connect?connected=${provider}`,
            error_redirect_uri: `${process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3010"}/connect?error=${provider}`,
          }),
        }
      );

      if (tokenRes.ok) {
        const tokenData = await tokenRes.json();
        return NextResponse.json({
          token: tokenData.token,
          expires_at: tokenData.expires_at,
          connect_link_url: tokenData.connect_link_url,
        });
      }

      const err = await tokenRes.text();
      console.error("Pipedream token error:", tokenRes.status, err);
    } catch (error) {
      console.error("Pipedream error:", error);
    }
  }

  // No Pipedream keys or Pipedream call failed — return without connect link
  // The integration record was still created as pending_auth
  return NextResponse.json({
    status: "pending_auth",
    message: pipedreamSecret
      ? "Pipedream token creation failed — integration saved as pending"
      : "Pipedream not configured — integration saved as pending. Add PIPEDREAM_CLIENT_SECRET to enable OAuth.",
  });
}
