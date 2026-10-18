import { NextResponse, type NextRequest } from "next/server";
import { createServiceClient } from "@/lib/supabase/server";
import { isPlanId, planForPriceId, verifyStripeSignature, type PlanId } from "@/lib/billing";

export const dynamic = "force-dynamic";

interface StripeEvent {
  id: string;
  type: string;
  data: { object: Record<string, unknown> };
}

interface StripeSubscriptionObject {
  id: string;
  customer: string;
  status: string;
  metadata?: Record<string, string>;
  current_period_end?: number;
  items?: { data?: Array<{ price?: { id?: string }; current_period_end?: number }> };
}

interface CheckoutSessionObject {
  id: string;
  mode?: string;
  customer?: string | null;
  subscription?: string | null;
  client_reference_id?: string | null;
  metadata?: Record<string, string>;
}

function toIso(seconds: number | undefined): string | null {
  return typeof seconds === "number" ? new Date(seconds * 1000).toISOString() : null;
}

/**
 * POST /api/billing/webhook
 * Stripe webhook: records plan + subscription status in public.billing_accounts.
 * Requires STRIPE_WEBHOOK_SECRET; returns 503 when unset.
 */
export async function POST(request: NextRequest) {
  const secret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!secret || !process.env.SUPABASE_SERVICE_ROLE_KEY) {
    return NextResponse.json({ error: "Billing webhook is not configured" }, { status: 503 });
  }

  const rawBody = await request.text();
  if (!verifyStripeSignature(rawBody, request.headers.get("stripe-signature"), secret)) {
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
  }

  let event: StripeEvent;
  try {
    event = JSON.parse(rawBody) as StripeEvent;
  } catch {
    return NextResponse.json({ error: "Invalid payload" }, { status: 400 });
  }

  const supabase = await createServiceClient();
  const now = new Date().toISOString();

  try {
    if (event.type === "checkout.session.completed") {
      const session = event.data.object as unknown as CheckoutSessionObject;
      const userId = session.client_reference_id || session.metadata?.user_id;
      if (session.mode !== "subscription" || !userId) {
        return NextResponse.json({ received: true, ignored: true });
      }
      const plan = isPlanId(session.metadata?.plan) ? session.metadata?.plan : null;
      const { error } = await supabase.from("billing_accounts").upsert(
        {
          user_id: userId,
          stripe_customer_id: session.customer ?? null,
          stripe_subscription_id: session.subscription ?? null,
          plan,
          status: "active",
          last_event_id: event.id,
          updated_at: now,
        },
        { onConflict: "user_id" }
      );
      if (error) throw error;
    } else if (
      event.type === "customer.subscription.created" ||
      event.type === "customer.subscription.updated" ||
      event.type === "customer.subscription.deleted"
    ) {
      const sub = event.data.object as unknown as StripeSubscriptionObject;
      const item = sub.items?.data?.[0];
      const plan: PlanId | null =
        (isPlanId(sub.metadata?.plan) ? (sub.metadata?.plan as PlanId) : undefined) ??
        planForPriceId(item?.price?.id) ??
        null;
      const status = event.type === "customer.subscription.deleted" ? "canceled" : sub.status;
      const periodEnd = toIso(sub.current_period_end ?? item?.current_period_end);

      let userId = sub.metadata?.user_id;
      if (!userId) {
        const { data } = await supabase
          .from("billing_accounts")
          .select("user_id")
          .eq("stripe_customer_id", sub.customer)
          .maybeSingle();
        userId = data?.user_id;
      }
      if (!userId) {
        // Not a MeetKai checkout; acknowledge so Stripe stops retrying.
        return NextResponse.json({ received: true, ignored: true });
      }

      const row: Record<string, unknown> = {
        user_id: userId,
        stripe_customer_id: sub.customer,
        stripe_subscription_id: sub.id,
        status,
        current_period_end: periodEnd,
        last_event_id: event.id,
        updated_at: now,
      };
      if (plan) row.plan = plan;
      const { error } = await supabase.from("billing_accounts").upsert(row, { onConflict: "user_id" });
      if (error) throw error;
    }
  } catch (error) {
    console.error("Stripe webhook handling failed", event.type, error);
    // 500 lets Stripe retry once the migration or env is fixed.
    return NextResponse.json({ error: "Webhook handling failed" }, { status: 500 });
  }

  return NextResponse.json({ received: true });
}
