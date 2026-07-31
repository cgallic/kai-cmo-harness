import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import { z } from "zod";
const querySchema = z.object({ brand_id: z.string().uuid(), post_id: z.string().uuid().optional(), limit: z.coerce.number().int().min(1).max(100).default(50) });
export async function GET(request: Request) {
  const supabase = await createClient(); const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const parsed = querySchema.safeParse(Object.fromEntries(new URL(request.url).searchParams)); if (!parsed.success) return NextResponse.json({ error: "Invalid query", issues: parsed.error.issues }, { status: 400 });
  const { brand_id, post_id, limit } = parsed.data;
  const { data: brand } = await supabase.from("brands").select("id").eq("id", brand_id).eq("user_id", user.id).maybeSingle(); if (!brand) return NextResponse.json({ error: "Brand not found" }, { status: 404 });
  let query = supabase.from("social_posts").select("*, social_post_media(*), social_provider_receipts(*)").eq("brand_id", brand_id).order("created_at", { ascending: false }).limit(limit);
  if (post_id) query = query.eq("id", post_id);
  const { data, error } = await query; if (error) return NextResponse.json({ error: "Failed to load social status" }, { status: 500 });
  return NextResponse.json({ posts: data ?? [] });
}
