import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const brandId = request.nextUrl.searchParams.get("brand_id");
  if (!brandId) return NextResponse.json({ error: "brand_id is required" }, { status: 400 });

  const { data: brand } = await supabase.from("brands").select("id").eq("id", brandId).eq("user_id", user.id).single();
  if (!brand) return NextResponse.json({ error: "Brand not found", code: "BRAND_NOT_FOUND" }, { status: 404 });

  const serviceClient = await createServiceClient();
  const { data: runs, error: runsError } = await serviceClient
    .from("agent_runs")
    .select("id, task_type, status, runtime_id, progress, started_at, completed_at, created_at")
    .eq("brand_id", brandId)
    .order("created_at", { ascending: false })
    .limit(25);
  if (runsError) return NextResponse.json({ error: "Failed to fetch agent status" }, { status: 500 });

  const runtimeIds = Array.from(new Set((runs ?? []).map((run) => run.runtime_id).filter(Boolean)));
  const { data: runtimes } = runtimeIds.length
    ? await serviceClient.from("runtimes").select("id, daemon_id, brand_id, name, status, last_heartbeat, updated_at").in("id", runtimeIds).eq("brand_id", brandId)
    : { data: [] };

  return NextResponse.json({ brand_id: brandId, runs: runs ?? [], runtimes: runtimes ?? [], timestamp: new Date().toISOString() });
}
