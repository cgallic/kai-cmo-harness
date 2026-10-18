import Link from "next/link";
import type { Metadata } from "next";
import { Check } from "lucide-react";
import { createClient } from "@/lib/supabase/server";
import { PLANS, getBillingAccount, hasPaidPlan, purchasablePlans, type BillingAccount } from "@/lib/billing";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Pricing",
  description: "MeetKai plans: Starter, Growth, and Full Stack.",
};

const NOTICES: Record<string, { tone: "error" | "info"; text: string }> = {
  cancelled: { tone: "info", text: "Checkout cancelled. No charge was made." },
  error: { tone: "error", text: "Checkout could not start. Try again, or email connor@kaicalls.com." },
};

export default async function PricingPage({
  searchParams,
}: {
  searchParams?: { billing?: string };
}) {
  const purchasable = purchasablePlans();

  let signedIn = false;
  let account: BillingAccount | null = null;
  if (process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
    try {
      const supabase = await createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (user) {
        signedIn = true;
        account = await getBillingAccount(supabase, user.id);
      }
    } catch {
      signedIn = false;
    }
  }
  const paid = hasPaidPlan(account);
  const notice = searchParams?.billing ? NOTICES[searchParams.billing] : undefined;

  return (
    <main className="min-h-screen px-4 py-12 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-10 flex items-center justify-between gap-4">
          <Link href={signedIn ? "/dashboard" : "/"} className="font-display text-xl font-bold">
            Meet<span className="text-amber">Kai</span>
          </Link>
          <Link
            href={signedIn ? "/dashboard" : "/#signin"}
            className="text-sm text-text-secondary hover:text-foreground"
          >
            {signedIn ? "Back to dashboard" : "Sign in"}
          </Link>
        </div>

        <header className="mb-10 max-w-2xl">
          <h1 className="font-display text-4xl font-bold">Pick the plan that fits where you are.</h1>
          <p className="mt-3 text-text-secondary">
            Month to month. No contracts. Ad spend is not included in plan pricing.
          </p>
          {paid && account?.plan && (
            <p className="mt-4 rounded-lg border border-success/40 bg-success-dim px-4 py-3 text-sm text-success">
              You are on the {PLANS.find((p) => p.id === account?.plan)?.name ?? account.plan} plan.
            </p>
          )}
          {notice && (
            <p
              className={cn(
                "mt-4 rounded-lg border px-4 py-3 text-sm",
                notice.tone === "error"
                  ? "border-error/40 bg-error-dim text-error"
                  : "border-info/40 bg-info-dim text-info"
              )}
            >
              {notice.text}
            </p>
          )}
        </header>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {PLANS.map((plan) => {
            const canBuy = purchasable.has(plan.id);
            const isCurrent = paid && account?.plan === plan.id;
            return (
              <section
                key={plan.id}
                className={cn(
                  "flex flex-col rounded-lg border bg-card p-6",
                  plan.featured ? "border-amber" : "border-border"
                )}
              >
                {plan.featured && (
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-amber">Most popular</p>
                )}
                <h2 className="text-xl font-semibold">{plan.name}</h2>
                <p className="mt-2">
                  <span className="font-mono text-4xl font-bold">{plan.price}</span>
                  <span className="text-text-secondary">/mo</span>
                </p>
                <p className="mt-2 text-sm text-text-secondary">{plan.description}</p>
                <ul className="mt-5 flex-1 space-y-2 text-sm">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex gap-2">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-amber" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>

                <div className="mt-6">
                  {isCurrent ? (
                    <p className="rounded-lg border border-border px-4 py-2.5 text-center text-sm text-text-secondary">
                      Current plan
                    </p>
                  ) : canBuy && signedIn ? (
                    <form action="/api/billing/checkout" method="POST">
                      <input type="hidden" name="plan" value={plan.id} />
                      <button
                        type="submit"
                        className={cn(
                          "w-full rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors",
                          plan.featured
                            ? "bg-amber text-background hover:bg-amber-light"
                            : "border border-border hover:border-border-hover hover:bg-bg-elevated"
                        )}
                      >
                        Choose {plan.name}
                      </button>
                    </form>
                  ) : canBuy ? (
                    <Link
                      href="/#signin"
                      className="block w-full rounded-lg border border-border px-4 py-2.5 text-center text-sm font-semibold hover:bg-bg-elevated"
                    >
                      Sign in to subscribe
                    </Link>
                  ) : (
                    <a
                      href="https://meetkai.xyz/platform#get-started"
                      className="block w-full rounded-lg border border-border px-4 py-2.5 text-center text-sm font-semibold hover:bg-bg-elevated"
                    >
                      Talk to us
                    </a>
                  )}
                </div>
              </section>
            );
          })}
        </div>
      </div>
    </main>
  );
}
