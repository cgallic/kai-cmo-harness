"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  CircleDot,
  Crosshair,
  FileCheck2,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";

import type {
  AutopilotCommandCenterResponse,
  PortfolioBrand,
} from "@/lib/gateway/types";
import { cn, timeAgo } from "@/lib/utils";

type LoadState = "loading" | "ready" | "unavailable";

function humanize(value: string) {
  return value.replace(/[_-]+/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function healthTone(health: string) {
  const normalized = health.toLowerCase();
  if (["healthy", "good", "excellent", "verified", "ready"].includes(normalized)) {
    return "border-success/25 bg-success-dim text-success";
  }
  if (["blocked", "critical", "failed", "unhealthy"].includes(normalized)) {
    return "border-error/25 bg-error-dim text-error";
  }
  return "border-amber/25 bg-amber-dim text-amber-light";
}

function EvidenceRefs({ refs, compact = false }: { refs: string[]; compact?: boolean }) {
  if (refs.length === 0) {
    return <span className="text-text-tertiary">No proof attached</span>;
  }

  const visible = compact ? refs.slice(0, 2) : refs;
  return (
    <span className="inline-flex flex-wrap gap-x-2 gap-y-1">
      {visible.map((ref) => (
        <code key={ref} className="font-mono text-[10px] text-info break-all">
          {ref}
        </code>
      ))}
      {compact && refs.length > visible.length && (
        <span className="text-[10px] text-text-tertiary">+{refs.length - visible.length} more</span>
      )}
    </span>
  );
}

function PortfolioCard({ brand }: { brand: PortfolioBrand }) {
  return (
    <article className="rounded-lg border border-border bg-background/55 p-4" aria-label={`${brand.brand_name} status`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-display text-lg font-semibold">{brand.brand_name}</h3>
          <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.18em] text-text-tertiary">
            {humanize(brand.lifecycle)}
          </p>
        </div>
        <span className={cn("rounded-full border px-2 py-1 font-mono text-[10px] uppercase", healthTone(brand.health))}>
          {humanize(brand.health)}
        </span>
      </div>
      <dl className="mt-4 grid gap-3 text-sm">
        <div>
          <dt className="text-[10px] font-bold uppercase tracking-[0.16em] text-text-tertiary">Blocked gate</dt>
          <dd className="mt-1 text-foreground">{humanize(brand.blocked_gate)}</dd>
        </div>
        <div>
          <dt className="text-[10px] font-bold uppercase tracking-[0.16em] text-text-tertiary">Owner</dt>
          <dd className="mt-1 text-foreground">{brand.owner}</dd>
        </div>
        <div>
          <dt className="text-[10px] font-bold uppercase tracking-[0.16em] text-text-tertiary">Next action</dt>
          <dd className="mt-1 text-text-secondary">{brand.next_action}</dd>
        </div>
        <div>
          <dt className="text-[10px] font-bold uppercase tracking-[0.16em] text-text-tertiary">Proof-bound close</dt>
          <dd className="mt-1 text-text-secondary">{brand.close_condition}</dd>
        </div>
      </dl>
    </article>
  );
}

export function AutopilotCommandCenter() {
  const [data, setData] = useState<AutopilotCommandCenterResponse | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");

  const load = useCallback(async () => {
    setLoadState("loading");
    try {
      const response = await fetch("/api/autopilot/command-center", { cache: "no-store" });
      if (!response.ok) throw new Error(`Command Center returned ${response.status}`);
      setData((await response.json()) as AutopilotCommandCenterResponse);
      setLoadState("ready");
    } catch {
      setData(null);
      setLoadState("unavailable");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const portfolio = data?.portfolio ?? [];
  const blockedCount = portfolio.filter(
    (brand) => brand.blocked_gate.toLowerCase() !== "none",
  ).length;

  if (loadState === "loading") {
    return (
      <section className="overflow-hidden rounded-xl border border-border bg-card" aria-busy="true" aria-label="Loading Autopilot Command Center">
        <div className="h-1 bg-amber/70" />
        <div className="grid gap-6 p-5 sm:p-7 lg:grid-cols-[1.45fr_0.55fr]">
          <div className="space-y-4">
            <div className="h-3 w-40 animate-pulse rounded bg-border" />
            <div className="h-12 max-w-xl animate-pulse rounded bg-bg-elevated" />
            <div className="h-24 animate-pulse rounded bg-bg-elevated" />
          </div>
          <div className="h-48 animate-pulse rounded-lg bg-bg-elevated" />
        </div>
      </section>
    );
  }

  if (loadState === "unavailable" || !data) {
    return (
      <section className="relative overflow-hidden rounded-xl border border-coral/25 bg-card p-5 sm:p-7" role="status">
        <div className="absolute inset-y-0 left-0 w-1 bg-coral" />
        <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
          <div className="flex gap-4">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-coral" />
            <div>
              <p className="font-mono text-[10px] font-bold uppercase tracking-[0.22em] text-coral">Live state unavailable</p>
              <h2 className="mt-2 font-display text-2xl font-semibold">Autopilot is not guessing.</h2>
              <p className="mt-1 max-w-2xl text-sm text-text-secondary">
                The verified operating ledger could not be read. Existing dashboard signals remain below, but no bottleneck is declared without evidence.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => void load()}
            className="inline-flex min-h-10 items-center justify-center gap-2 rounded-lg border border-border bg-bg-elevated px-4 text-sm font-semibold text-foreground transition-colors hover:border-border-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber"
          >
            <RefreshCw className="h-4 w-4" /> Retry read-back
          </button>
        </div>
      </section>
    );
  }

  const bottleneck = data.primary_bottleneck;
  const coach = data.coach;

  return (
    <section className="space-y-4" aria-labelledby="autopilot-title">
      <div className="overflow-hidden rounded-xl border border-border bg-card shadow-[0_20px_70px_rgba(0,0,0,0.24)]">
        <div className="h-1 bg-gradient-to-r from-amber via-info to-coral" />
        <div className="grid lg:grid-cols-[minmax(0,1.55fr)_minmax(280px,0.65fr)]">
          <div className="relative overflow-hidden p-5 sm:p-7 lg:p-9">
            <div className="pointer-events-none absolute -right-20 -top-24 h-64 w-64 rounded-full border border-amber/10 bg-amber/5" />
            <div className="relative">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="inline-flex items-center gap-2 font-mono text-[10px] font-bold uppercase tracking-[0.24em] text-amber-light">
                  <Crosshair className="h-3.5 w-3.5" /> Company Autopilot / primary constraint
                </p>
                <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-text-tertiary">
                  Read back {timeAgo(data.timestamp)}
                </span>
              </div>

              {bottleneck ? (
                <>
                  <div className="mt-7 flex items-start gap-4">
                    <span className="mt-1 flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-coral/30 bg-coral-dim text-coral">
                      <CircleDot className="h-5 w-5" />
                    </span>
                    <div>
                      <p className="font-mono text-xs uppercase tracking-[0.16em] text-text-tertiary">
                        {bottleneck.brand_name} · {humanize(bottleneck.lifecycle)}
                      </p>
                      <h1 id="autopilot-title" className="mt-2 max-w-4xl font-display text-3xl font-bold leading-[1.06] sm:text-5xl">
                        {humanize(bottleneck.blocked_gate)}
                      </h1>
                      {bottleneck.summary && (
                        <p className="mt-3 max-w-3xl text-base leading-relaxed text-text-secondary">{bottleneck.summary}</p>
                      )}
                    </div>
                  </div>

                  <div className="mt-8 grid gap-px overflow-hidden rounded-lg border border-border bg-border sm:grid-cols-3">
                    <div className="bg-background/90 p-4">
                      <p className="font-mono text-[10px] uppercase tracking-[0.17em] text-text-tertiary">Owner</p>
                      <p className="mt-2 text-sm font-semibold">{bottleneck.owner}</p>
                    </div>
                    <div className="bg-background/90 p-4 sm:col-span-2">
                      <p className="font-mono text-[10px] uppercase tracking-[0.17em] text-text-tertiary">Do this next</p>
                      <p className="mt-2 flex gap-2 text-sm font-semibold text-amber-light">
                        <ArrowRight className="mt-0.5 h-4 w-4 shrink-0" /> {bottleneck.next_action}
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 flex items-start gap-3 rounded-lg border border-success/20 bg-success-dim px-4 py-3">
                    <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                    <div>
                      <p className="font-mono text-[10px] uppercase tracking-[0.17em] text-success">Close only when</p>
                      <p className="mt-1 text-sm text-foreground">{bottleneck.close_condition}</p>
                      <div className="mt-2 text-xs"><EvidenceRefs refs={bottleneck.evidence_refs} /></div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="mt-8 flex items-start gap-4">
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-success/30 bg-success-dim text-success">
                    <CheckCircle2 className="h-5 w-5" />
                  </span>
                  <div>
                    <h1 id="autopilot-title" className="font-display text-3xl font-bold sm:text-5xl">No proof-bound constraint.</h1>
                    <p className="mt-3 max-w-2xl text-text-secondary">Every currently observed gate has acceptable evidence. Autopilot will surface one constraint when verified state changes.</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          <aside className="border-t border-border bg-bg-elevated/70 p-5 sm:p-7 lg:border-l lg:border-t-0" aria-label="Implementation coach">
            <div className="flex items-center justify-between gap-3">
              <p className="font-mono text-[10px] font-bold uppercase tracking-[0.22em] text-info">Implementation coach</p>
              <span className={cn("rounded-full border px-2 py-1 font-mono text-[9px] uppercase", healthTone(coach.state))}>
                {humanize(coach.state)}
              </span>
            </div>
            <p className="mt-5 font-display text-xl font-semibold leading-snug">{coach.message}</p>
            <div className="mt-6 space-y-5 border-l border-border pl-4">
              <div>
                <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-text-tertiary">Verified next action</p>
                <p className="mt-1 text-sm text-text-secondary">{coach.next_action}</p>
              </div>
              <div>
                <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-text-tertiary">Acceptance evidence</p>
                <p className="mt-1 text-sm text-text-secondary">{coach.close_condition}</p>
              </div>
              <div>
                <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-text-tertiary">Evidence ledger</p>
                <div className="mt-2 text-xs"><EvidenceRefs refs={coach.evidence_refs} /></div>
              </div>
            </div>
          </aside>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card p-4 sm:p-6">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="font-mono text-[10px] font-bold uppercase tracking-[0.22em] text-text-tertiary">Agency portfolio / live gate ledger</p>
            <h2 className="mt-1 font-display text-2xl font-semibold">{portfolio.length} companies. {blockedCount} blocked.</h2>
          </div>
          <p className="max-w-md text-right text-xs text-text-tertiary">Lifecycle labels describe observed state. Close conditions require evidence, not a checked box.</p>
        </div>

        {portfolio.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border px-6 py-10 text-center">
            <FileCheck2 className="mx-auto h-6 w-6 text-text-tertiary" />
            <p className="mt-3 text-sm text-text-secondary">No companies have durable operating context yet.</p>
          </div>
        ) : (
          <>
            <div className="grid gap-3 md:hidden">
              {portfolio.map((brand) => <PortfolioCard key={brand.brand_id} brand={brand} />)}
            </div>
            <div className="hidden overflow-x-auto md:block">
              <table className="w-full min-w-[1080px] border-collapse text-left text-sm">
                <thead>
                  <tr className="border-y border-border font-mono text-[9px] uppercase tracking-[0.16em] text-text-tertiary">
                    <th scope="col" className="px-3 py-3 font-medium">Company / lifecycle</th>
                    <th scope="col" className="px-3 py-3 font-medium">Health</th>
                    <th scope="col" className="px-3 py-3 font-medium">Blocked gate</th>
                    <th scope="col" className="px-3 py-3 font-medium">Owner</th>
                    <th scope="col" className="px-3 py-3 font-medium">Next action</th>
                    <th scope="col" className="px-3 py-3 font-medium">Proof-bound close</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolio.map((brand) => (
                    <tr key={brand.brand_id} className="border-b border-border/70 align-top transition-colors hover:bg-bg-elevated/60">
                      <th scope="row" className="px-3 py-4 font-normal">
                        <span className="block font-display text-base font-semibold text-foreground">{brand.brand_name}</span>
                        <span className="mt-1 block font-mono text-[9px] uppercase tracking-[0.14em] text-text-tertiary">{humanize(brand.lifecycle)}</span>
                      </th>
                      <td className="px-3 py-4">
                        <span className={cn("inline-flex rounded-full border px-2 py-1 font-mono text-[9px] uppercase", healthTone(brand.health))}>{humanize(brand.health)}</span>
                      </td>
                      <td className="max-w-[150px] px-3 py-4 font-medium text-foreground">{humanize(brand.blocked_gate)}</td>
                      <td className="max-w-[120px] px-3 py-4 text-text-secondary">{brand.owner}</td>
                      <td className="max-w-[220px] px-3 py-4 text-text-secondary">{brand.next_action}</td>
                      <td className="max-w-[280px] px-3 py-4">
                        <p className="text-text-secondary">{brand.close_condition}</p>
                        <div className="mt-2"><EvidenceRefs refs={brand.evidence_refs} compact /></div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
