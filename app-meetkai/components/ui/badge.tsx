import { cn } from "@/lib/utils";
import { statusColor, statusBgColor } from "@/lib/utils";

interface BadgeProps {
  status: string;
  label?: string;
  className?: string;
}

export function Badge({ status, label, className }: BadgeProps) {
  const displayLabel = label || status.replace(/_/g, " ");

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full capitalize",
        statusBgColor(status),
        statusColor(status),
        className
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full", statusColor(status).replace("text-", "bg-"))} />
      {displayLabel}
    </span>
  );
}

interface RiskBadgeProps {
  tier: "low" | "medium" | "high";
  className?: string;
}

export function RiskBadge({ tier, className }: RiskBadgeProps) {
  const colors = {
    low: "bg-success-dim text-success",
    medium: "bg-amber-dim text-amber",
    high: "bg-error-dim text-error",
  };

  return (
    <span className={cn("inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-full capitalize", colors[tier], className)}>
      {tier} risk
    </span>
  );
}
