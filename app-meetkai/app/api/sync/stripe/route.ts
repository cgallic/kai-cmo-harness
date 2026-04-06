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

interface StripeBalance {
  available: { amount: number; currency: string }[];
  pending: { amount: number; currency: string }[];
}

interface StripeCharge {
  id: string;
  amount: number;
  currency: string;
  status: string;
  created: number;
}

interface StripeChargesResponse {
  data?: StripeCharge[];
}

interface StripePlan {
  amount: number | null;
  interval: string;
}

interface StripeSubscription {
  id: string;
  status: string;
  plan: StripePlan;
}

interface StripeSubscriptionsResponse {
  data?: StripeSubscription[];
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
    .eq("provider", "stripe")
    .eq("status", "connected")
    .order("created_at", { ascending: false })
    .limit(1);

  if (!integrations || integrations.length === 0) {
    return NextResponse.json({ error: "Stripe not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const integration = integrations[0];
  if (!integration.connected_account_id) {
    return NextResponse.json({ error: "Stripe not connected", code: "NOT_CONNECTED" }, { status: 404 });
  }

  const accountId = integration.connected_account_id;

  try {
    const pd = getPd();

    // Fetch balance
    const balanceRes = await pd.proxy.get({
      url: "https://api.stripe.com/v1/balance",
      accountId,
      externalUserId: brand_id,
    });
    const balanceData = ((balanceRes as { data?: StripeBalance })?.data ?? balanceRes) as StripeBalance;

    const balanceAvailable = (balanceData.available || []).reduce((sum, b) => sum + b.amount, 0) / 100;
    const balancePending = (balanceData.pending || []).reduce((sum, b) => sum + b.amount, 0) / 100;

    // Fetch recent charges (last 100)
    const chargesRes = await pd.proxy.get({
      url: "https://api.stripe.com/v1/charges?limit=100",
      accountId,
      externalUserId: brand_id,
    });
    const chargesData = ((chargesRes as { data?: StripeChargesResponse })?.data ?? chargesRes) as StripeChargesResponse;
    const charges = chargesData?.data || [];

    // Calculate total revenue from charges in last 28 days
    const twentyEightDaysAgo = Math.floor(Date.now() / 1000) - 28 * 24 * 60 * 60;
    const recentCharges = charges.filter(
      (c) => c.status === "succeeded" && c.created >= twentyEightDaysAgo
    );
    const totalRevenue28d = recentCharges.reduce((sum, c) => sum + c.amount, 0) / 100;

    // Fetch active subscriptions
    const subsRes = await pd.proxy.get({
      url: "https://api.stripe.com/v1/subscriptions?status=active&limit=100",
      accountId,
      externalUserId: brand_id,
    });
    const subsData = ((subsRes as { data?: StripeSubscriptionsResponse })?.data ?? subsRes) as StripeSubscriptionsResponse;
    const subscriptions = subsData?.data || [];

    // Calculate MRR: monthly plans contribute plan.amount/100, yearly plans contribute plan.amount/1200
    const mrr = subscriptions.reduce((sum, sub) => {
      const amount = sub.plan?.amount ?? 0;
      if (sub.plan?.interval === "year") {
        return sum + amount / 1200;
      }
      return sum + amount / 100;
    }, 0);

    // Build last 10 recent charges for snapshot
    const recentChargesSnapshot = charges.slice(0, 10).map((c) => ({
      amount: c.amount / 100,
      status: c.status,
      created: c.created,
    }));

    const snapshot = {
      mrr: Math.round(mrr * 100) / 100,
      total_revenue_28d: Math.round(totalRevenue28d * 100) / 100,
      active_subscriptions: subscriptions.length,
      balance_available: balanceAvailable,
      balance_pending: balancePending,
      recent_charges: recentChargesSnapshot,
    };

    await serviceClient.from("channel_snapshots").insert({
      brand_id,
      channel: "payments",
      provider: "stripe",
      snapshot_data: snapshot,
    });

    await serviceClient
      .from("integrations")
      .update({ last_sync_at: new Date().toISOString() })
      .eq("id", integration.id);

    return NextResponse.json({ status: "synced", data: snapshot });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Stripe sync error:", message);
    return NextResponse.json({ error: "Sync failed", code: "SYNC_FAILED", detail: message }, { status: 500 });
  }
}
