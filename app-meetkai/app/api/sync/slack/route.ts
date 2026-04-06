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

interface SlackTeamResponse {
  ok?: boolean;
  team?: { id: string; name: string; domain: string };
}

interface SlackMember {
  id: string;
  is_bot?: boolean;
  deleted?: boolean;
}

interface SlackUsersResponse {
  ok?: boolean;
  members?: SlackMember[];
}

interface SlackChannel {
  id: string;
  name: string;
}

interface SlackConversationsResponse {
  ok?: boolean;
  channels?: SlackChannel[];
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
    .eq("provider", "slack")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "Slack not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "Slack not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;

  try {
    const pd = getPd();

    // Fetch workspace info
    const teamRes = await pd.proxy.get({
      url: "https://slack.com/api/team.info",
      accountId,
      externalUserId: brand_id,
    });
    const teamData = ((teamRes as { data?: SlackTeamResponse })?.data ?? teamRes) as SlackTeamResponse;

    // Fetch members (non-bot, non-deleted)
    const usersRes = await pd.proxy.get({
      url: "https://slack.com/api/users.list?limit=200",
      accountId,
      externalUserId: brand_id,
    });
    const usersData = ((usersRes as { data?: SlackUsersResponse })?.data ?? usersRes) as SlackUsersResponse;
    const activeMembers = (usersData?.members || []).filter((m) => !m.is_bot && !m.deleted);

    // Fetch public channels
    const channelsRes = await pd.proxy.get({
      url: "https://slack.com/api/conversations.list?types=public_channel&exclude_archived=true&limit=200",
      accountId,
      externalUserId: brand_id,
    });
    const channelsData = ((channelsRes as { data?: SlackConversationsResponse })?.data ?? channelsRes) as SlackConversationsResponse;

    const snapshot = {
      workspace_name: teamData?.team?.name || "Unknown",
      workspace_domain: teamData?.team?.domain || "",
      members_count: activeMembers.length,
      channels_count: channelsData?.channels?.length || 0,
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "notifications",
      provider: "slack",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Slack sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
