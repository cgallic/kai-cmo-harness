import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import { z } from "zod";
const schema = z.object({ brand_id: z.string().uuid(), post_id: z.string().uuid() });
export async function POST(request: Request) {
  const supabase = await createClient(); const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const parsed = schema.safeParse(await request.json()); if (!parsed.success) return NextResponse.json({ error: "Invalid request body" }, { status: 400 });
  const { brand_id, post_id } = parsed.data;
  const { data: post } = await supabase.from("social_posts").update({ status: "approved", approved_at: new Date().toISOString(), approved_by: user.id }).eq("id", post_id).eq("brand_id", brand_id).eq("status", "draft").select("*").maybeSingle();
  if (!post) return NextResponse.json({ error: "Draft post not found" }, { status: 404 });
  return NextResponse.json({ post });
}
