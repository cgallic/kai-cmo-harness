import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

export function formatPercent(n: number): string {
  return `${n.toFixed(1)}%`;
}

export function timeAgo(date: string): string {
  const seconds = Math.floor((Date.now() - new Date(date).getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(date).toLocaleDateString();
}

export function scoreColor(score: number): string {
  if (score >= 70) return "text-success";
  if (score >= 40) return "text-amber";
  return "text-error";
}

export function statusColor(status: string): string {
  switch (status) {
    case "connected":
    case "completed":
    case "approved":
    case "auto_approved":
    case "executed":
    case "verified":
    case "learned":
    case "operational":
      return "text-success";
    case "pending":
    case "pending_auth":
    case "executing":
    case "needs_setup":
    case "drafted":
    case "gated":
      return "text-amber";
    case "degraded":
    case "held":
      return "text-amber";
    case "disconnected":
    case "error":
    case "failed":
    case "rejected":
    case "rolled_back":
      return "text-error";
    default:
      return "text-text-tertiary";
  }
}

export function statusBgColor(status: string): string {
  switch (status) {
    case "connected":
    case "completed":
    case "approved":
    case "executed":
    case "verified":
    case "learned":
    case "operational":
      return "bg-success-dim";
    case "pending":
    case "pending_auth":
    case "executing":
    case "needs_setup":
    case "drafted":
    case "gated":
      return "bg-amber-dim";
    case "degraded":
    case "held":
      return "bg-amber-dim";
    default:
      return "bg-error-dim";
  }
}

export function riskTierColor(tier: string): string {
  switch (tier) {
    case "low": return "text-success";
    case "medium": return "text-amber";
    case "high": return "text-error";
    default: return "text-text-tertiary";
  }
}

export function riskTierBgColor(tier: string): string {
  switch (tier) {
    case "low": return "bg-success-dim";
    case "medium": return "bg-amber-dim";
    case "high": return "bg-error-dim";
    default: return "bg-border";
  }
}
