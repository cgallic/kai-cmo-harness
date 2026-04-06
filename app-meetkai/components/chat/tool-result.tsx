"use client";

import { cn } from "@/lib/utils";
import { Check, X, BarChart3, FileText, Search } from "lucide-react";

interface ToolResultProps {
  toolName: string;
  result: Record<string, unknown>;
}

export function ToolResult({ toolName, result }: ToolResultProps) {
  if (result.error) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-error-dim rounded-lg text-xs text-error">
        <X className="w-3.5 h-3.5 flex-shrink-0" />
        <span>{String(result.error)}</span>
      </div>
    );
  }

  switch (toolName) {
    case "get_score": {
      const score = result.score as number | null;
      return (
        <div className="flex items-center gap-3 px-3 py-2.5 bg-bg-elevated rounded-lg">
          <BarChart3 className="w-4 h-4 text-amber" />
          <div>
            <span
              className={cn(
                "font-mono font-bold text-lg",
                score != null && score >= 70
                  ? "text-success"
                  : score != null && score >= 40
                    ? "text-amber"
                    : "text-error",
              )}
            >
              {score != null ? `${Math.round(score)}/100` : "No score"}
            </span>
            {result.finding_count != null && (
              <span className="text-xs text-text-tertiary ml-2">
                {String(result.finding_count)} findings
              </span>
            )}
          </div>
        </div>
      );
    }
    case "generate_content":
    case "run_skill": {
      const data = result.data as Record<string, unknown> | undefined;
      return (
        <div className="flex items-center gap-2 px-3 py-2.5 bg-bg-elevated rounded-lg text-xs">
          <FileText className="w-4 h-4 text-amber flex-shrink-0" />
          <div>
            <p className="text-sm font-medium">Job queued</p>
            {data?.job_id != null && (
              <p className="text-text-tertiary">ID: {String(data.job_id)}</p>
            )}
          </div>
        </div>
      );
    }
    case "run_audit": {
      return (
        <div className="flex items-center gap-2 px-3 py-2.5 bg-bg-elevated rounded-lg text-xs">
          <Search className="w-4 h-4 text-amber flex-shrink-0" />
          <span className="text-sm">Audit running...</span>
        </div>
      );
    }
    default:
      return (
        <div className="flex items-center gap-2 px-3 py-2.5 bg-bg-elevated rounded-lg text-xs">
          <Check className="w-3.5 h-3.5 text-success flex-shrink-0" />
          <span className="text-text-secondary truncate">
            {JSON.stringify(result).slice(0, 100)}
          </span>
        </div>
      );
  }
}
