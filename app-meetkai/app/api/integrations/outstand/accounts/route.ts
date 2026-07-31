import { listAccounts } from "@/lib/providers/outstand";
import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import { z } from "zod";

const schema = z.object({ brand_id: z.string().uuid() });

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const parsed = schema.safeParse(await request.json());
  if (!parsed.success) return NextResponse.json({ error: "Invalid request body" }, { status: 400 });

  const { brand_id } = parsed.data;
  const { data: brand } = await supabase.from("brands").select("id").eq("id", brand_id).eq("user_id", user.id).maybeSingle();
  if (!brand) return NextResponse.json({ error: "Brand not found" }, { status: 404 });

  try {
    const accounts = await listAccounts();
    const service = await createServiceClient();
    const { error } = await service.from("integrations").upsert({
      brand_id, channel: "social", provider: "outstand", status: "connected",
      connected_account_id: accounts[0]?.id || null,
      capabilities: ["connect", "list_accounts", "create_post", "schedule_post", "read_post", "cancel_post"],
      config: { account_ids: accounts.map((account) => account.id) },
      metadata: { account_count: accounts.length, last_account_sync_at: new Date().toISOString() },
      connected_at: new Date().toISOString(), last_sync_at: new Date().toISOString(), updated_at: new Date().toISOString(),
    }, { onConflict: "brand_id,channel,provider" });
    if (error) throw error;
    return NextResponse.json({ accounts, count: accounts.length, verified: true });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Outstand account sync failed" }, { status: 502 });
  }
}
