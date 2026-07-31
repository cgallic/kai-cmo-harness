import { createServiceClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

const heartbeatSchema = z.object({
  daemon_id: z.string().min(1).max(200),
  name: z.string().min(1).max(200),
  brand_id: z.string().uuid().optional(),
  status: z.enum(["online", "offline", "draining"]).default("online"),
  host_info: z.record(z.string(), z.unknown()).default({}),
});

function authorized(request: NextRequest) {
  const expected = process.env.AGENT_HEARTBEAT_TOKEN;
  return Boolean(expected && request.headers.get("authorization") === `Bearer ${expected}`);
}

export async function POST(request: NextRequest) {
  if (!authorized(request)) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const parsed = heartbeatSchema.safeParse(await request.json());
  if (!parsed.success) return NextResponse.json({ error: "Invalid request body", issues: parsed.error.issues }, { status: 400 });

  const serviceClient = await createServiceClient();
  const { data, error } = await serviceClient
    .from("runtimes")
    .upsert({
      ...parsed.data,
      last_heartbeat: new Date().toISOString(),
    }, { onConflict: "daemon_id" })
    .select("id, daemon_id, brand_id, name, status, last_heartbeat, updated_at")
    .single();

  if (error) {
    console.error("Agent heartbeat error:", error.message);
    return NextResponse.json({ error: "Failed to record heartbeat" }, { status: 500 });
  }
  return NextResponse.json({ runtime: data });
}
