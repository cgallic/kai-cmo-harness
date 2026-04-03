import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

const PIPEDREAM_API = "https://api.pipedream.com/v1";

export async function POST(request: Request) {
  // Verify authenticated user
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
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

  try {
    // Create Pipedream connect token
    const tokenRes = await fetch(`${PIPEDREAM_API}/connect/tokens`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.PIPEDREAM_CLIENT_SECRET}`,
      },
      body: JSON.stringify({
        external_user_id: brand_id,
        ...(app_slug ? { app: app_slug } : {}),
        allowed_origins: [process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3010"],
        success_redirect_uri: `${process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3010"}/connect?connected=${provider}`,
        error_redirect_uri: `${process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3010"}/connect?error=${provider}`,
      }),
    });

    if (!tokenRes.ok) {
      const err = await tokenRes.text();
      console.error("Pipedream token error:", err);
      return NextResponse.json({ error: "Failed to create connect token" }, { status: 502 });
    }

    const tokenData = await tokenRes.json();

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

    return NextResponse.json({
      token: tokenData.token,
      expires_at: tokenData.expires_at,
      connect_link_url: tokenData.connect_link_url,
    });
  } catch (error) {
    console.error("Connection error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
