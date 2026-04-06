import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

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

  const { data: integrations } = await serviceClient
    .from("integrations")
    .select("*")
    .eq("brand_id", brand_id)
    .eq("provider", "squarespace")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "Squarespace not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const snapshot = {
    connected: true,
    synced_at: new Date().toISOString(),
  };

  await serviceClient.from("channel_snapshots").insert({
    brand_id,
    channel: "website",
    provider: "squarespace",
    snapshot_data: snapshot,
  });

  await serviceClient
    .from("integrations")
    .update({ last_sync_at: new Date().toISOString() })
    .eq("id", integrations[0].id);

  return NextResponse.json({ status: "synced", data: snapshot });
}
