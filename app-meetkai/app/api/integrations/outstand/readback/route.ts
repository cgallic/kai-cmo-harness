import { getPost } from "@/lib/providers/outstand";
import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import { z } from "zod";

const schema = z.object({ brand_id: z.string().uuid(), post_id: z.string().uuid(), provider_post_id: z.string().min(1) });

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const parsed = schema.safeParse(await request.json());
  if (!parsed.success) return NextResponse.json({ error: "Invalid request body" }, { status: 400 });
  const { brand_id, post_id, provider_post_id } = parsed.data;
  const { data: post } = await supabase.from("social_posts").select("id").eq("id", post_id).eq("brand_id", brand_id).maybeSingle();
  if (!post) return NextResponse.json({ error: "Post not found" }, { status: 404 });

  try {
    const providerPost = await getPost(provider_post_id);
    const statuses = providerPost.socialAccounts || [];
    const failed = statuses.some((account) => account.status === "failed");
    const published = statuses.length > 0 && statuses.every((account) => account.status === "published");
    const status = failed ? "failed" : published ? "published" : "publishing";
    const service = await createServiceClient();
    const { error } = await service.from("social_provider_receipts").update({
      status, provider_post_id, provider_url: null, response: providerPost,
      error: failed ? statuses.find((account) => account.error)?.error || "Outstand publish failed" : null,
      published_at: providerPost.publishedAt || null, updated_at: new Date().toISOString(),
    }).eq("brand_id", brand_id).eq("post_id", post_id).eq("provider", "outstand");
    if (error) throw error;
    if (status === "published") await service.from("social_posts").update({ status, updated_at: new Date().toISOString() }).eq("id", post_id).eq("brand_id", brand_id);
    return NextResponse.json({ status, verified: true, provider_post: providerPost });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Outstand read-back failed", verified: false }, { status: 502 });
  }
}
