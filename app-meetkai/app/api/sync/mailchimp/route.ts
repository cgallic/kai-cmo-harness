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

interface MailchimpList {
  id: string;
  name: string;
  stats: {
    member_count: number;
    unsubscribe_count: number;
    open_rate: number;
    click_rate: number;
    campaign_count: number;
  };
}

interface MailchimpListsResponse {
  lists?: MailchimpList[];
  total_items?: number;
}

interface MailchimpCampaignReport {
  id: string;
  campaign_title: string;
  emails_sent: number;
  opens: { open_rate: number; unique_opens: number };
  clicks: { click_rate: number; unique_clicks: number };
  unsubscribed: number;
  bounces: { hard_bounces: number; soft_bounces: number };
}

interface MailchimpReportsResponse {
  reports?: MailchimpCampaignReport[];
  total_items?: number;
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
    .eq("provider", "mailchimp")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "Mailchimp not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "Mailchimp not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;

  try {
    const pd = getPd();

    // Mailchimp API requires the datacenter prefix in the URL.
    // Pipedream handles this via the proxy — the SDK resolves the correct dc.
    // We use the generic api.mailchimp.com endpoint; Pipedream rewrites it.

    // Fetch all audiences (lists)
    const listsRes = await pd.proxy.get({
      url: "https://server.api.mailchimp.com/3.0/lists?count=100&fields=lists.id,lists.name,lists.stats,total_items",
      accountId,
      externalUserId: brand_id,
    });

    const listsData = ((listsRes as { data?: MailchimpListsResponse })?.data ?? listsRes) as MailchimpListsResponse;
    const lists = listsData?.lists || [];

    const audiences = lists.map((l) => ({
      id: l.id,
      name: l.name,
      subscriber_count: l.stats.member_count,
      unsubscribe_count: l.stats.unsubscribe_count,
      open_rate: Math.round(l.stats.open_rate * 100) / 100,
      click_rate: Math.round(l.stats.click_rate * 100) / 100,
      campaign_count: l.stats.campaign_count,
    }));

    const totalSubscribers = audiences.reduce((sum, a) => sum + a.subscriber_count, 0);
    const avgOpenRate = audiences.length > 0
      ? Math.round(audiences.reduce((sum, a) => sum + a.open_rate, 0) / audiences.length * 100) / 100
      : 0;
    const avgClickRate = audiences.length > 0
      ? Math.round(audiences.reduce((sum, a) => sum + a.click_rate, 0) / audiences.length * 100) / 100
      : 0;

    // Fetch recent campaign reports (last 10)
    const reportsRes = await pd.proxy.get({
      url: "https://server.api.mailchimp.com/3.0/reports?count=10&sort_field=send_time&sort_dir=DESC&fields=reports.id,reports.campaign_title,reports.emails_sent,reports.opens,reports.clicks,reports.unsubscribed,reports.bounces,total_items",
      accountId,
      externalUserId: brand_id,
    });

    const reportsData = ((reportsRes as { data?: MailchimpReportsResponse })?.data ?? reportsRes) as MailchimpReportsResponse;
    const reports = (reportsData?.reports || []).map((r) => ({
      id: r.id,
      title: r.campaign_title,
      emails_sent: r.emails_sent,
      open_rate: Math.round(r.opens.open_rate * 100) / 100,
      unique_opens: r.opens.unique_opens,
      click_rate: Math.round(r.clicks.click_rate * 100) / 100,
      unique_clicks: r.clicks.unique_clicks,
      unsubscribes: r.unsubscribed,
      bounces: r.bounces.hard_bounces + r.bounces.soft_bounces,
    }));

    const snapshot = {
      total_subscribers: totalSubscribers,
      audience_count: audiences.length,
      avg_open_rate: avgOpenRate,
      avg_click_rate: avgClickRate,
      audiences,
      recent_campaigns: reports,
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "email",
      provider: "mailchimp",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Mailchimp sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
