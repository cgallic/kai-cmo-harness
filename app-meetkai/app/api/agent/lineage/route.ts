import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

const lineageSchema = z.object({
  brand_id: z.string().uuid(),
  action_id: z.string().uuid().optional(),
  agent_run_id: z.string().uuid().optional(),
  task_id: z.string().max(200).optional(),
  event_type: z.string().min(1).max(100),
  payload: z.record(z.string(), z.unknown()).default({}),
}).refine((value) => value.action_id || value.agent_run_id || value.task_id, "A lineage parent is required");

function authorized(request: NextRequest) {
  const expected = process.env.AGENT_HEARTBEAT_TOKEN;
  return Boolean(expected && request.headers.get("authorization") === `Bearer ${expected}`);
}

export async function POST(request: NextRequest) {
  if (!authorized(request)) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const parsed = lineageSchema.safeParse(await request.json());
  if (!parsed.success) return NextResponse.json({ error: "Invalid request body", issues: parsed.error.issues }, { status: 400 });
  const serviceClient = await createServiceClient();
  if (parsed.data.action_id) {
    const { data } = await serviceClient.from("actions").select("id").eq("id", parsed.data.action_id).eq("brand_id", parsed.data.brand_id).single();
    if (!data) return NextResponse.json({ error: "Action not found", code: "ACTION_NOT_FOUND" }, { status: 404 });
  }
  if (parsed.data.agent_run_id) {
    const { data } = await serviceClient.from("agent_runs").select("id").eq("id", parsed.data.agent_run_id).eq("brand_id", parsed.data.brand_id).single();
    if (!data) return NextResponse.json({ error: "Agent run not found", code: "AGENT_RUN_NOT_FOUND" }, { status: 404 });
  }
  const { data, error } = await serviceClient.from("action_task_lineage").insert(parsed.data).select().single();
  if (error) return NextResponse.json({ error: "Failed to record lineage" }, { status: 500 });
  return NextResponse.json({ lineage: data }, { status: 201 });
}

export async function GET(request: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const brandId = request.nextUrl.searchParams.get("brand_id");
  if (!brandId) return NextResponse.json({ error: "brand_id is required" }, { status: 400 });
  const { data: brand } = await supabase.from("brands").select("id").eq("id", brandId).eq("user_id", user.id).single();
  if (!brand) return NextResponse.json({ error: "Brand not found", code: "BRAND_NOT_FOUND" }, { status: 404 });
  const { data, error } = await supabase.from("action_task_lineage").select("*").eq("brand_id", brandId).order("created_at", { ascending: false }).limit(100);
  if (error) return NextResponse.json({ error: "Failed to fetch lineage" }, { status: 500 });
  return NextResponse.json({ brand_id: brandId, lineage: data ?? [] });
}
