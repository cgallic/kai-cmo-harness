import { NextResponse, type NextRequest } from "next/server";
import { createClient, createServiceClient } from "@/lib/supabase/server";
import { isBillingEnabled, isPlanId, priceIdFor, stripeRequest } from "@/lib/billing";

export const dynamic = "force-dynamic";

function appOrigin(request: NextRequest): string {
  return (process.env.NEXT_PUBLIC_APP_URL || request.nextUrl.origin).replace(/\/$/, "");
}

/**
 * POST /api/billing/checkout  (form field or JSON body: plan=starter|growth|scale)
 * Creates a Stripe Checkout Session in subscription mode and 303-redirects to it.
 * Returns 503 when billing env vars are unset.
 */
export async function POST(request: NextRequest) {
  if (!isBillingEnabled()) {
    return NextResponse.json({ error: "Billing is not configured" }, { status: 503 });
  }

  const origin = appOrigin(request);
  const contentType = request.headers.get("content-type") || "";
  let plan: unknown;
  const wantsJson = contentType.includes("application/json");
  if (wantsJson) {
    plan = (await request.json().catch(() => ({})))?.plan;
  } else {
    plan = (await request.formData().catch(() => null))?.get("plan");
  }

  if (!isPlanId(plan)) {
    return NextResponse.json({ error: "Unknown plan" }, { status: 400 });
  }
  const priceId = priceIdFor(plan);
  if (!priceId) {
    return NextResponse.json({ error: "Plan is not available" }, { status: 503 });
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.redirect(`${origin}/#signin`, { status: 303 });
  }

  // Reuse the Stripe customer if this user has checked out before.
  let customerId: string | undefined;
  try {
    const service = await createServiceClient();
    const { data } = await service
      .from("billing_accounts")
      .select("stripe_customer_id")
      .eq("user_id", user.id)
      .maybeSingle();
    customerId = data?.stripe_customer_id || undefined;
  } catch {
    customerId = undefined;
  }

  try {
    const session = await stripeRequest<{ id: string; url: string | null }>("POST", "checkout/sessions", {
      mode: "subscription",
      "line_items[0][price]": priceId,
      "line_items[0][quantity]": 1,
      client_reference_id: user.id,
      customer: customerId,
      customer_email: customerId ? undefined : user.email,
      "metadata[user_id]": user.id,
      "metadata[plan]": plan,
      "subscription_data[metadata][user_id]": user.id,
      "subscription_data[metadata][plan]": plan,
      allow_promotion_codes: true,
      success_url: `${origin}/settings?billing=success`,
      cancel_url: `${origin}/pricing?billing=cancelled`,
    });

    if (!session.url) throw new Error("Stripe returned no checkout URL");
    if (wantsJson) return NextResponse.json({ url: session.url });
    return NextResponse.redirect(session.url, { status: 303 });
  } catch (error) {
    console.error("Stripe checkout failed", error);
    if (wantsJson) {
      return NextResponse.json({ error: "Could not start checkout" }, { status: 502 });
    }
    return NextResponse.redirect(`${origin}/pricing?billing=error`, { status: 303 });
  }
}
