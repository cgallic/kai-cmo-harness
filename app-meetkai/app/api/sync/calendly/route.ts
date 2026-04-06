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

interface CalendlyUserResponse {
  resource?: {
    uri?: string;
    name?: string;
  };
}

interface CalendlyEventsResponse {
  collection?: unknown[];
  pagination?: { count?: number };
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
    .eq("provider", "calendly")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "Calendly not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "Calendly not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;

  try {
    const pd = getPd();

    // Get current user URI first
    const meRes = await pd.proxy.get({
      url: "https://api.calendly.com/users/me",
      accountId,
      externalUserId: brand_id,
    });

    const meData = ((meRes as { data?: CalendlyUserResponse })?.data ?? meRes) as CalendlyUserResponse;
    const userUri = meData?.resource?.uri;

    if (!userUri) {
      return NextResponse.json({ error: "Could not resolve Calendly user", code: "NO_USER" }, { status: 404 });
    }

    const now = new Date();
    const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    // Fetch upcoming active events and events from last 30 days
    const [upcomingRes, pastRes] = await Promise.all([
      pd.proxy.get({
        url: `https://api.calendly.com/scheduled_events?user=${encodeURIComponent(userUri)}&status=active&count=100&min_start_time=${now.toISOString()}`,
        accountId,
        externalUserId: brand_id,
      }),
      pd.proxy.get({
        url: `https://api.calendly.com/scheduled_events?user=${encodeURIComponent(userUri)}&count=100&min_start_time=${thirtyDaysAgo.toISOString()}&max_start_time=${now.toISOString()}`,
        accountId,
        externalUserId: brand_id,
      }),
    ]);

    const upcomingData = ((upcomingRes as { data?: CalendlyEventsResponse })?.data ?? upcomingRes) as CalendlyEventsResponse;
    const pastData = ((pastRes as { data?: CalendlyEventsResponse })?.data ?? pastRes) as CalendlyEventsResponse;

    const snapshot = {
      upcoming_events: upcomingData?.collection?.length ?? 0,
      total_events_30d: pastData?.collection?.length ?? 0,
      event_types_count: 0, // Calendly doesn't return this in events endpoint
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "scheduling",
      provider: "calendly",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Calendly sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
