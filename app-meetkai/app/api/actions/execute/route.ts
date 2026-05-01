import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import { generateContent, getGenerateJob } from "@/lib/gateway/generate";
import { z } from "zod";

const executeRequestSchema = z.object({
  action_id: z.string().uuid(),
});

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const parsed = executeRequestSchema.safeParse(await request.json());
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid request body", issues: parsed.error.issues }, { status: 400 });
  }
  const { action_id } = parsed.data;

  // Read action via user session (RLS ensures ownership)
  const { data: action, error: actionErr } = await supabase
    .from("actions")
    .select("*, brands!inner(name, url)")
    .eq("id", action_id)
    .single();

  if (actionErr || !action) {
    return NextResponse.json({ error: "Action not found" }, { status: 404 });
  }

  if (action.approval_state !== "approved") {
    return NextResponse.json({ error: "Action must be approved before execution" }, { status: 400 });
  }

  const serviceClient = await createServiceClient();
  const currentMetadata = asRecord(action.metadata);

  // Mark as executing
  await serviceClient
    .from("actions")
    .update({
      execution_state: "executing",
      metadata: { ...currentMetadata, operating_state: "approved" },
    })
    .eq("id", action_id);

  try {
    // Determine content format from action type
    const format = mapActionTypeToFormat(action.action_type);
    const brand = action.brands as { name: string; url: string | null };
    const proposed = asRecord(action.proposed_changes);
    const requestedWorkflow = typeof proposed.workflow_id === "string" ? proposed.workflow_id : format;

    // Call gateway content engine
    const job = await generateContent({
      format: requestedWorkflow,
      site: brand.name.toLowerCase().replace(/\s+/g, "-"),
      keyword:
        (typeof proposed.finding === "string" && proposed.finding) ||
        action.intent ||
        action.action_type,
      brand_id: action.brand_id,
    });

    // Poll for completion (up to 90 seconds)
    let result = await getGenerateJob(job.job_id);
    let attempts = 0;
    while (result.status === "pending" || result.status === "running") {
      if (attempts++ > 18) break; // 18 * 5s = 90s
      await new Promise((r) => setTimeout(r, 5000));
      result = await getGenerateJob(job.job_id);
    }

    if (result.status === "completed") {
      const resultRecord = asRecord(result.result);
      const deliverable =
        typeof resultRecord.content_preview === "string"
          ? resultRecord.content_preview
          : typeof result.result === "string"
            ? result.result
            : JSON.stringify(result.result);
      const artifactIds = Array.isArray(result.artifact_ids)
        ? result.artifact_ids
        : result.artifacts?.map((a) => a.artifact_id) || [];

      await serviceClient
        .from("actions")
        .update({
          execution_state: "completed",
          result_summary: {
            gateway_job_id: job.job_id,
            gateway_run_id: result.run_id,
            deliverable,
            artifacts: artifactIds,
            workflow: result.workflow,
            approval_state: result.approval_state,
          },
          metadata: { ...currentMetadata, operating_state: "executed" },
          gateway_job_id: job.job_id,
          executed_at: new Date().toISOString(),
        })
        .eq("id", action_id);

      return NextResponse.json({ status: "completed", job_id: job.job_id, result: result.result });
    }

    // Job still running or failed
    await serviceClient
      .from("actions")
      .update({
        execution_state: result.status === "failed" ? "failed" : "executing",
        result_summary: { gateway_job_id: job.job_id, error: result.error },
        metadata: {
          ...currentMetadata,
          operating_state: result.status === "failed" ? "gated" : "approved",
        },
        gateway_job_id: job.job_id,
      })
      .eq("id", action_id);

    return NextResponse.json({
      status: result.status,
      job_id: job.job_id,
      message: result.status === "failed" ? result.error : "Still processing — check back shortly",
    });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);

    await serviceClient
      .from("actions")
      .update({
        execution_state: "failed",
        result_summary: { error: message },
        metadata: { ...currentMetadata, operating_state: "gated" },
      })
      .eq("id", action_id);

    return NextResponse.json({ status: "failed", error: message }, { status: 500 });
  }
}

function mapActionTypeToFormat(actionType: string): string {
  switch (actionType) {
    case "update_copy":
    case "fix_cta": return "landing-page";
    case "setup_kaicalls":
    case "improve_speed_to_lead": return "call-script";
    case "publish_gbp_update": return "gbp-post";
    case "draft_review_responses": return "review-response";
    case "launch_review_request_sequence": return "review-request-sequence";
    case "add_schema": return "blog";
    case "improve_seo": return "blog";
    case "improve_speed": return "blog";
    default: return "blog";
  }
}
