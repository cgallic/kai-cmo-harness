"use client";

import { cn, scoreColor } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import type { Audit } from "@/lib/types";
import { Search } from "lucide-react";

interface AuditScoreRingProps {
  audit: Audit | null;
  brandUrl?: string | null;
  brandId?: string;
  onAuditComplete?: (audit: Audit) => void;
  running?: boolean;
  onRunAudit?: () => void;
}

export function AuditScoreRing({
  audit,
  brandUrl,
  brandId,
  onAuditComplete: _onAuditComplete,
  running,
  onRunAudit,
}: AuditScoreRingProps) {
  // Suppress unused variable warning — kept for future callback wiring
  void _onAuditComplete;
  void brandId;

  const score = audit?.overall_score ?? 0;
  const circumference = 2 * Math.PI * 45;
  const progress = (score / 100) * circumference;

  const ringColor = score >= 70 ? "#22c55e" : score >= 40 ? "#f59e0b" : "#ef4444";

  const categories = audit?.category_scores
    ? Object.entries(audit.category_scores).map(([key, value]) => ({
        name: key.replace(/_/g, " "),
        score: value as number,
      }))
    : [];

  const showEmptyState = !audit && !running;
  const hasUrl = Boolean(brandUrl);

  return (
    <div className="card">
      <h3 className="section-title mb-6">Audit Score</h3>

      {running ? (
        <div className="flex flex-col items-center justify-center py-8 gap-4">
          <svg className="animate-spin h-10 w-10 text-amber" viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          <div className="text-center">
            <p className="text-sm font-medium text-foreground">Running audit...</p>
            <p className="text-xs text-text-tertiary mt-1">
              This can take 10-30 seconds. Analyzing your site now.
            </p>
          </div>
        </div>
      ) : showEmptyState ? (
        <div className="flex flex-col items-center justify-center py-8 gap-4">
          <div className="relative w-32 h-32 flex-shrink-0">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="45" fill="none" stroke="#1e1e1e" strokeWidth="6" />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="font-mono text-3xl font-bold text-text-tertiary">—</span>
            </div>
          </div>
          {hasUrl ? (
            <div className="text-center">
              <p className="text-text-tertiary text-sm mb-3">
                No audit data yet. Run your first audit to see your marketing score.
              </p>
              <Button onClick={onRunAudit} size="md">
                <Search className="w-4 h-4" />
                Run your first audit
              </Button>
            </div>
          ) : (
            <p className="text-text-tertiary text-sm text-center">
              Add a website URL in{" "}
              <a href="/settings" className="text-amber hover:underline">
                Settings
              </a>{" "}
              to run an audit.
            </p>
          )}
        </div>
      ) : (
        <div className="flex items-center gap-8">
          {/* Ring */}
          <div className="relative w-32 h-32 flex-shrink-0">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="45" fill="none" stroke="#1e1e1e" strokeWidth="6" />
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke={ringColor}
                strokeWidth="6"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={circumference - progress}
                className="transition-all duration-1000 ease-out"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className={cn("font-mono text-3xl font-bold", scoreColor(score))}>
                {Math.round(score)}
              </span>
            </div>
          </div>

          {/* Category breakdown */}
          <div className="flex-1 space-y-2.5">
            {categories.length > 0 ? (
              categories.map((cat) => (
                <div key={cat.name} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-text-secondary capitalize">{cat.name}</span>
                    <span className={cn("font-mono", scoreColor(cat.score * 10))}>
                      {cat.score.toFixed(1)}
                    </span>
                  </div>
                  <div className="h-1.5 bg-border rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{
                        width: `${cat.score * 10}%`,
                        backgroundColor:
                          cat.score >= 7 ? "#22c55e" : cat.score >= 4 ? "#f59e0b" : "#ef4444",
                      }}
                    />
                  </div>
                </div>
              ))
            ) : (
              <p className="text-text-tertiary text-sm">
                No category data available for this audit.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
