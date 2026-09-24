import { createHmac, timingSafeEqual } from "crypto";
import type { SupabaseClient } from "@supabase/supabase-js";

/**
 * Minimal Stripe billing for MeetKai plans.
 *
 * Everything here is inert until STRIPE_SECRET_KEY and at least one
 * STRIPE_PRICE_* env var are set: pricing buttons hide, the checkout route
 * returns 503, and the webhook route refuses requests.
 *
 * Talks to the Stripe REST API with fetch so the app needs no extra SDK.
 */

export const PLAN_IDS = ["starter", "growth", "scale"] as const;
export type PlanId = (typeof PLAN_IDS)[number];

export interface Plan {
  id: PlanId;
  name: string;
  price: string;
  description: string;
  features: string[];
  priceEnv: string;
  featured?: boolean;
}

// Mirrors the /platform plans on meetkai.xyz.
export const PLANS: Plan[] = [
  {
    id: "starter",
    name: "Starter",
    price: "$99",
    description: "Get online and start capturing leads.",
    priceEnv: "STRIPE_PRICE_STARTER",
    features: [
      "AI-built professional website",
      "Dedicated business phone number",
      "AI receptionist (up to 100 calls/mo)",
      "Basic CRM with lead tracking",
      "Email notifications for new leads",
      "Custom domain and SSL included",
    ],
  },
  {
    id: "growth",
    name: "Growth",
    price: "$299",
    description: "Drive traffic and convert the leads you get.",
    priceEnv: "STRIPE_PRICE_GROWTH",
    featured: true,
    features: [
      "Everything in Starter, plus:",
      "SEO and local search optimization",
      "AI content engine (blog and social)",
      "Advanced CRM with lead scoring",
      "Analytics dashboard and weekly reports",
      "Up to 500 AI calls/month",
      "Automated follow-up sequences",
    ],
  },
  {
    id: "scale",
    name: "Full Stack",
    price: "$599",
    description: "Your complete AI marketing department.",
    priceEnv: "STRIPE_PRICE_SCALE",
    features: [
      "Everything in Growth, plus:",
      "Google Ads campaign management",
      "Meta/Facebook Ads management",
      "AI cold email outreach",
      "Full CMO strategy and execution",
      "Unlimited AI calls",
      "Priority support and onboarding",
      "Competitive intelligence reports",
    ],
  },
];

/** Subscription statuses that count as a paid plan. */
export const PAID_STATUSES = new Set(["active", "trialing"]);

export function isPlanId(value: unknown): value is PlanId {
  return typeof value === "string" && (PLAN_IDS as readonly string[]).includes(value);
}

export function priceIdFor(plan: PlanId): string | undefined {
  const def = PLANS.find((p) => p.id === plan);
  const value = def ? process.env[def.priceEnv] : undefined;
  return value && value.trim() ? value.trim() : undefined;
}

export function planForPriceId(priceId: string | undefined | null): PlanId | undefined {
  if (!priceId) return undefined;
  return PLAN_IDS.find((plan) => priceIdFor(plan) === priceId);
}

/** True when checkout can run for at least one plan. */
export function isBillingEnabled(): boolean {
  return Boolean(process.env.STRIPE_SECRET_KEY) && PLAN_IDS.some((p) => priceIdFor(p));
}

/** Plans that can actually be purchased with the current env. */
export function purchasablePlans(): Set<PlanId> {
  if (!process.env.STRIPE_SECRET_KEY) return new Set();
  return new Set(PLAN_IDS.filter((p) => priceIdFor(p)));
}

type FormValue = string | number | boolean | undefined | null;

/** Encode a flat map of Stripe form params (keys already in bracket form). */
function encodeForm(params: Record<string, FormValue>): string {
  const body = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    body.append(key, String(value));
  }
  return body.toString();
}

export async function stripeRequest<T>(
  method: "GET" | "POST",
  path: string,
  params: Record<string, FormValue> = {}
): Promise<T> {
  const key = process.env.STRIPE_SECRET_KEY;
  if (!key) throw new Error("STRIPE_SECRET_KEY is not set");

  const encoded = encodeForm(params);
  const url = `https://api.stripe.com/v1/${path}${method === "GET" && encoded ? `?${encoded}` : ""}`;
  const res = await fetch(url, {
    method,
    headers: {
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: method === "POST" ? encoded : undefined,
    cache: "no-store",
  });

  const json = (await res.json().catch(() => ({}))) as T & { error?: { message?: string } };
  if (!res.ok) {
    throw new Error(json.error?.message || `Stripe request failed (${res.status})`);
  }
  return json;
}

/**
 * Verify a Stripe-Signature header (t=...,v1=...) against the raw body.
 * Returns false on any mismatch or when the timestamp is outside tolerance.
 */
export function verifyStripeSignature(
  rawBody: string,
  header: string | null,
  secret: string,
  toleranceSeconds = 300
): boolean {
  if (!header || !secret) return false;

  let timestamp = "";
  const signatures: string[] = [];
  for (const part of header.split(",")) {
    const [k, v] = part.split("=", 2);
    if (k === "t") timestamp = v;
    if (k === "v1" && v) signatures.push(v);
  }
  if (!timestamp || signatures.length === 0) return false;

  const ts = Number(timestamp);
  if (!Number.isFinite(ts) || Math.abs(Date.now() / 1000 - ts) > toleranceSeconds) return false;

  const expected = createHmac("sha256", secret).update(`${timestamp}.${rawBody}`, "utf8").digest("hex");
  const expectedBuf = Buffer.from(expected, "hex");
  return signatures.some((sig) => {
    const sigBuf = Buffer.from(sig, "hex");
    return sigBuf.length === expectedBuf.length && timingSafeEqual(sigBuf, expectedBuf);
  });
}

export interface BillingAccount {
  plan: PlanId | null;
  status: string | null;
  current_period_end: string | null;
}

export function hasPaidPlan(account: BillingAccount | null | undefined): boolean {
  return Boolean(account?.plan && account.status && PAID_STATUSES.has(account.status));
}

/**
 * Read the signed-in user's billing row. Returns null when the table does not
 * exist yet (migration not applied) or on any read error, so callers never crash.
 */
export async function getBillingAccount(supabase: SupabaseClient, userId: string): Promise<BillingAccount | null> {
  try {
    const { data, error } = await supabase
      .from("billing_accounts")
      .select("plan, status, current_period_end")
      .eq("user_id", userId)
      .maybeSingle();
    if (error || !data) return null;
    return data as BillingAccount;
  } catch {
    return null;
  }
}
