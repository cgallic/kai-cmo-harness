import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import { PipedreamClient } from "@pipedream/sdk";

function getPipedreamClient() {
  return new PipedreamClient({
    projectId: process.env.PIPEDREAM_PROJECT_ID!,
    projectEnvironment: (process.env.PIPEDREAM_ENVIRONMENT as "development" | "production") || "development",
    clientId: process.env.PIPEDREAM_CLIENT_ID!,
    clientSecret: process.env.PIPEDREAM_CLIENT_SECRET!,
  });
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await request.json();
  const { brand_id, channel, provider } = body;

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

  // Create Pipedream connect token
  if (!process.env.PIPEDREAM_CLIENT_ID || !process.env.PIPEDREAM_CLIENT_SECRET) {
    return NextResponse.json({
      status: "pending_auth",
      message: "Pipedream not configured",
    });
  }

  try {
    const pd = getPipedreamClient();
    const appUrl = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3010";

    const result = await pd.tokens.create({
      externalUserId: brand_id,
      successRedirectUri: `${appUrl}/connect?connected=${provider}`,
      errorRedirectUri: `${appUrl}/connect?error=${provider}`,
    });

    return NextResponse.json({
      token: result.token,
      expires_at: result.expiresAt,
      connect_link_url: result.connectLinkUrl,
    });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Pipedream SDK error:", message);
    return NextResponse.json(
      { error: "Failed to create connect token", detail: message },
      { status: 502 }
    );
  }
}
