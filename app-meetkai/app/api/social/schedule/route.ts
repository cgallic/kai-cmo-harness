import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import { z } from "zod";
const schema = z.object({ brand_id: z.string().uuid(), post_id: z.string().uuid(), scheduled_at: z.string().datetime() });
export async function POST(request: Request) {
  const supabase = await createClient(); const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const parsed = schema.safeParse(await request.json()); if (!parsed.success) return NextResponse.json({ error: "Invalid request body", issues: parsed.error.issues }, { status: 400 });
  const { brand_id, post_id, scheduled_at } = parsed.data;
  const { data: post } = await supabase.from("social_posts").update({ status: "scheduled", scheduled_at }).eq("id", post_id).eq("brand_id", brand_id).in("status", ["approved", "scheduled"]).select("*").maybeSingle();
  if (!post) return NextResponse.json({ error: "Approved post not found" }, { status: 404 });
  return NextResponse.json({ post });
}
