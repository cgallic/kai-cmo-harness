import { createClient, createServiceClient } from "@/lib/supabase/server";
import { gateway } from "@/lib/gateway/client";
import { NextResponse } from "next/server";
import { z } from "zod";

const schema = z.object({
  brand_id: z.string().uuid(),
  post_id: z.string().uuid(),
  scheduled: z.boolean().optional().default(false),
});

type SocialPost = {
  id: string;
  brand_id: string;
  status: string;
  caption: string;
  platforms: string[];
  scheduled_at: string | null;
  metadata: Record<string, unknown>;
  social_post_media: { media_url: string; media_type: string; sort_order: number }[];
};

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const parsed = schema.safeParse(await request.json());
  if (!parsed.success) return NextResponse.json({ error: "Invalid request body", issues: parsed.error.issues }, { status: 400 });
  const { brand_id, post_id, scheduled } = parsed.data;

  const { data: post, error } = await supabase
    .from("social_posts")
    .select("*, social_post_media(media_url, media_type, sort_order)")
    .eq("id", post_id)
    .eq("brand_id", brand_id)
    .in("status", scheduled ? ["scheduled"] : ["approved"])
    .maybeSingle<SocialPost>();
  if (error || !post) return NextResponse.json({ error: "Approved post not found" }, { status: 404 });

  const actionType = scheduled ? "schedule_social_post" : "publish_social_post";
  const proposedChanges = {
    post: {
      caption: post.caption,
      platforms: post.platforms,
      scheduled_at: post.scheduled_at,
      media: [...(post.social_post_media || [])].sort((a, b) => a.sort_order - b.sort_order),
    },
    provider: "outstand",
    post_id,
  };

  try {
    const proposal = await gateway<{ action_id: string }>("/ops/propose", {
      method: "POST",
      params: { brand_id, channel: "social", action_type: actionType, intent: `${scheduled ? "Schedule" : "Publish"} MeetKai social post ${post_id}` },
      body: proposedChanges,
    });
    const approval = await gateway<{ action_id: string; approval_state: string }>(`/ops/proposals/${proposal.action_id}/approve`, {
      method: "POST",
      body: { note: `Approved by MeetKai user ${user.id}` },
    });

    const service = await createServiceClient();
    const metadata = { ...(post.metadata || {}), action_id: approval.action_id, provider: "outstand" };
    await service.from("social_posts").update({ status: "publishing", action_id: approval.action_id, metadata }).eq("id", post_id).eq("brand_id", brand_id);
    await service.from("social_provider_receipts").upsert({
      post_id, brand_id, provider: "outstand", action_id: approval.action_id, status: "pending", response: { action_id: approval.action_id },
    }, { onConflict: "post_id,provider" });
    return NextResponse.json({ status: "queued", action_id: approval.action_id, approval_state: approval.approval_state });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: "Social action could not be queued", detail: message }, { status: 502 });
  }
}
