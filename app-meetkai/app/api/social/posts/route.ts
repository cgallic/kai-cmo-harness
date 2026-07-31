import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import { z } from "zod";

const schema = z.object({
  brand_id: z.string().uuid(), caption: z.string().trim().min(1).max(5000),
  platforms: z.array(z.string().trim().min(1)).min(1).max(10),
  scheduled_at: z.string().datetime().nullable().optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
  media: z.array(z.object({ media_url: z.string().url(), media_type: z.enum(["image", "video"]).default("image"), sort_order: z.number().int().min(0).optional(), metadata: z.record(z.string(), z.unknown()).optional() })).max(20).optional(),
});

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const parsed = schema.safeParse(await request.json());
  if (!parsed.success) return NextResponse.json({ error: "Invalid request body", issues: parsed.error.issues }, { status: 400 });
  const { brand_id, media, ...post } = parsed.data;
  const { data: brand } = await supabase.from("brands").select("id").eq("id", brand_id).eq("user_id", user.id).maybeSingle();
  if (!brand) return NextResponse.json({ error: "Brand not found" }, { status: 404 });
  const { data: created, error } = await supabase.from("social_posts").insert({ brand_id, ...post }).select("*").single();
  if (error || !created) return NextResponse.json({ error: "Failed to create social post" }, { status: 500 });
  if (media?.length) {
    const { error: mediaError } = await supabase.from("social_post_media").insert(media.map((item, index) => ({ post_id: created.id, media_url: item.media_url, media_type: item.media_type, sort_order: item.sort_order ?? index, metadata: item.metadata ?? {} })));
    if (mediaError) return NextResponse.json({ error: "Post created but media failed", post: created }, { status: 500 });
  }
  return NextResponse.json({ post: created }, { status: 201 });
}
