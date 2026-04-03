"use client";

import { cn, scoreColor } from "@/lib/utils";
import type { Audit } from "@/lib/types";

interface AuditScoreRingProps {
  audit: Audit | null;
}

export function AuditScoreRing({ audit }: AuditScoreRingProps) {
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

  return (
    <div className="card">
      <h3 className="section-title mb-6">Audit Score</h3>

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
                      backgroundColor: cat.score >= 7 ? "#22c55e" : cat.score >= 4 ? "#f59e0b" : "#ef4444",
                    }}
                  />
                </div>
              </div>
            ))
          ) : (
            <p className="text-text-tertiary text-sm">No audit data yet. Run an audit to see your score.</p>
          )}
        </div>
      </div>
    </div>
  );
}
