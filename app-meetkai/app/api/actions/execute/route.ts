import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import { generateContent, getGenerateJob } from "@/lib/gateway/generate";

interface ExecuteRequest {
  action_id: string;
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body: ExecuteRequest = await request.json();
  const { action_id } = body;

  if (!action_id) {
    return NextResponse.json({ error: "action_id is required" }, { status: 400 });
  }

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

  // Mark as executing
  await serviceClient
    .from("actions")
    .update({ execution_state: "executing" })
    .eq("id", action_id);

  try {
    // Determine content format from action type
    const format = mapActionTypeToFormat(action.action_type);
    const brand = action.brands as { name: string; url: string | null };
    const proposed = action.proposed_changes as Record<string, string>;

    // Call gateway content engine
    const job = await generateContent({
      format,
      site: brand.name.toLowerCase().replace(/\s+/g, "-"),
      keyword: proposed.finding || action.intent || action.action_type,
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
      await serviceClient
        .from("actions")
        .update({
          execution_state: "completed",
          result_summary: {
            gateway_job_id: job.job_id,
            deliverable: typeof result.result === "string" ? result.result : JSON.stringify(result.result),
            artifacts: result.artifacts?.map((a) => a.artifact_id) || [],
          },
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
      })
      .eq("id", action_id);

    return NextResponse.json({ status: "failed", error: message }, { status: 500 });
  }
}

function mapActionTypeToFormat(actionType: string): string {
  switch (actionType) {
    case "update_copy":
    case "fix_cta": return "landing-page";
    case "add_schema": return "blog";
    case "improve_seo": return "blog";
    case "improve_speed": return "blog";
    default: return "blog";
  }
}
