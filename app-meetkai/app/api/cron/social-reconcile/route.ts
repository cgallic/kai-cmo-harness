import { createServiceClient } from "@/lib/supabase/server";
import { gateway, GatewayError } from "@/lib/gateway/client";
import { NextResponse } from "next/server";

type ActionRecord = {
  execution_state?: string;
  operating_state?: string;
  result_summary?: Record<string, unknown>;
  verification_result?: Record<string, unknown>;
};

export async function GET(request: Request) {
  if (request.headers.get("authorization") !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const service = await createServiceClient();
  const { data: posts, error } = await service
    .from("social_posts")
    .select("id, brand_id, action_id, status")
    .in("status", ["publishing", "scheduled"])
    .not("action_id", "is", null)
    .limit(100);
  if (error) return NextResponse.json({ error: "Failed to load social queue" }, { status: 500 });

  const results: { post_id: string; status: string; action_id: string }[] = [];
  for (const post of posts || []) {
    const actionId = String(post.action_id);
    try {
      const action = await gateway<ActionRecord>(`/ops/actions/${actionId}`);
      const verified = action.operating_state === "verified" || action.verification_result?.status === "verified";
      const failed = action.execution_state === "failed";
      const nextStatus = verified ? "published" : failed ? "failed" : post.status;
      const verification = action.verification_result || action.result_summary || {};
      if (nextStatus !== post.status || verified || failed) {
        await service.from("social_posts").update({
          status: nextStatus,
          metadata: { action_state: action.execution_state, verification },
        }).eq("id", post.id).eq("brand_id", post.brand_id);
        await service.from("social_provider_receipts").update({
          status: verified ? "published" : failed ? "failed" : "publishing",
          provider_post_id: typeof verification.post_id === "string" ? verification.post_id : undefined,
          provider_url: typeof verification.provider_url === "string" ? verification.provider_url : undefined,
          error: failed ? JSON.stringify(action.result_summary || {}) : null,
          response: verification,
          published_at: verified ? new Date().toISOString() : null,
        }).eq("post_id", post.id).eq("provider", "outstand");
      }
      results.push({ post_id: post.id, action_id: actionId, status: nextStatus });
    } catch (err) {
      const status = err instanceof GatewayError && err.status === 404 ? "missing_action" : "gateway_error";
      results.push({ post_id: post.id, action_id: actionId, status });
    }
  }
  return NextResponse.json({ status: "completed", reconciled: results.length, results });
}
