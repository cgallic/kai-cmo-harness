import { createClient, createServiceClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";
import { PipedreamClient } from "@pipedream/sdk";

function getPd() {
  return new PipedreamClient({
    projectId: process.env.PIPEDREAM_PROJECT_ID!,
    projectEnvironment:
      (process.env.PIPEDREAM_ENVIRONMENT as "development" | "production") || "development",
    clientId: process.env.PIPEDREAM_CLIENT_ID!,
    clientSecret: process.env.PIPEDREAM_CLIENT_SECRET!,
  });
}

interface CkSubscribersResponse {
  total_subscribers?: number;
}

interface CkSequencesResponse {
  courses?: unknown[];
}

interface CkAutomationsResponse {
  automations?: unknown[];
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { brand_id } = await request.json();

  const { data: brand } = await supabase
    .from("brands")
    .select("id")
    .eq("id", brand_id)
    .eq("user_id", user.id)
    .single();

  if (!brand) {
    return NextResponse.json({ error: "Brand not found" }, { status: 404 });
  }

  const serviceClient = await createServiceClient();

  const { data: integrations } = await serviceClient
    .from("integrations")
    .select("*")
    .eq("brand_id", brand_id)
    .eq("provider", "convertkit")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "ConvertKit not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "ConvertKit not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;

  try {
    const pd = getPd();

    const [subsRes, seqRes, autoRes] = await Promise.all([
      pd.proxy.get({
        url: "https://api.convertkit.com/v3/subscribers",
        accountId,
        externalUserId: brand_id,
      }),
      pd.proxy.get({
        url: "https://api.convertkit.com/v3/sequences",
        accountId,
        externalUserId: brand_id,
      }),
      pd.proxy.get({
        url: "https://api.convertkit.com/v3/automations",
        accountId,
        externalUserId: brand_id,
      }),
    ]);

    const subsData = ((subsRes as { data?: CkSubscribersResponse })?.data ?? subsRes) as CkSubscribersResponse;
    const seqData = ((seqRes as { data?: CkSequencesResponse })?.data ?? seqRes) as CkSequencesResponse;
    const autoData = ((autoRes as { data?: CkAutomationsResponse })?.data ?? autoRes) as CkAutomationsResponse;

    const snapshot = {
      subscriber_count: subsData?.total_subscribers ?? 0,
      sequences_count: seqData?.courses?.length ?? 0,
      automations_count: autoData?.automations?.length ?? 0,
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "email",
      provider: "convertkit",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("ConvertKit sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
