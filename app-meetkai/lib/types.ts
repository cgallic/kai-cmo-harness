export interface Brand {
  id: string;
  user_id: string;
  name: string;
  url: string | null;
  description: string | null;
  archetype: string;
  active_channels: string[];
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Audit {
  id: string;
  brand_id: string;
  overall_score: number | null;
  category_scores: Record<string, number>;
  findings: AuditFinding[];
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface AuditFinding {
  category: string;
  severity: "critical" | "warning" | "info" | "pass";
  title: string;
  description: string;
  recommendation?: string;
}

export interface Integration {
  id: string;
  brand_id: string;
  channel: string;
  provider: string;
  status: IntegrationStatus;
  connected_account_id: string | null;
  capabilities: string[];
  config: Record<string, unknown>;
  metadata: Record<string, unknown>;
  connected_at: string | null;
  last_sync_at: string | null;
  created_at: string;
  updated_at: string;
}

export type IntegrationStatus =
  | "pending_auth"
  | "connected"
  | "degraded"
  | "disconnected"
  | "error";

export interface Action {
  id: string;
  brand_id: string;
  action_type: string;
  channel: string;
  intent: string | null;
  approval_state: ApprovalState;
  execution_state: ExecutionState;
  risk_tier: "low" | "medium" | "high";
  proposed_changes: Record<string, unknown>;
  result_summary: Record<string, unknown> | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  executed_at: string | null;
}

export type ApprovalState =
  | "pending"
  | "approved"
  | "rejected"
  | "auto_approved"
  | "held";

export type ExecutionState =
  | "pending"
  | "executing"
  | "completed"
  | "failed"
  | "rolled_back";

export interface ChannelSnapshot {
  id: string;
  brand_id: string;
  channel: string;
  provider: string;
  snapshot_data: Record<string, unknown>;
  created_at: string;
}

// Provider mapping (mirrors gateway/adapters/pipedream/base.py)
export const PROVIDERS: ProviderConfig[] = [
  // Analytics
  { channel: "analytics", provider: "ga4", name: "Google Analytics", icon: "BarChart3", appSlug: "google_analytics" },
  { channel: "analytics", provider: "gsc", name: "Google Search Console", icon: "Search", appSlug: "google_search_console" },
  { channel: "analytics", provider: "gbp", name: "Google Business", icon: "MapPin", appSlug: "google_my_business" },
  // Website
  { channel: "website", provider: "wordpress", name: "WordPress", icon: "Globe", appSlug: "wordpress_org" },
  { channel: "website", provider: "shopify", name: "Shopify", icon: "ShoppingBag", appSlug: "shopify" },
  // Social
  { channel: "social", provider: "facebook", name: "Facebook", icon: "Facebook", appSlug: "facebook_pages" },
  { channel: "social", provider: "instagram", name: "Instagram", icon: "Instagram", appSlug: "instagram_business" },
  { channel: "social", provider: "linkedin", name: "Linkedin", icon: "Linkedin", appSlug: "linkedin" },
  { channel: "social", provider: "tiktok", name: "TikTok", icon: "Music", appSlug: "tiktok_marketing" },
  { channel: "social", provider: "youtube", name: "YouTube", icon: "Youtube", appSlug: "youtube_data_api" },
  // Email
  { channel: "email", provider: "mailchimp", name: "Mailchimp", icon: "Mail", appSlug: "mailchimp" },
  { channel: "email", provider: "sendgrid", name: "SendGrid", icon: "Send", appSlug: "sendgrid" },
  // Paid Media
  { channel: "paid_media", provider: "google_ads", name: "Google Ads", icon: "Megaphone", appSlug: "google_ads" },
  { channel: "paid_media", provider: "meta_ads", name: "Meta Ads", icon: "Target", appSlug: "facebook_marketing_api" },
];

export interface ProviderConfig {
  channel: string;
  provider: string;
  name: string;
  icon: string;
  appSlug: string;
}

// Channel category groupings for the connect page
export const CHANNEL_CATEGORIES: Record<string, string[]> = {
  Analytics: ["analytics"],
  Website: ["website"],
  Social: ["social"],
  Email: ["email"],
  "Paid Media": ["paid_media"],
};
