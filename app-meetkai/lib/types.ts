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
  capability_state?: IntegrationCapabilityState;
  operational?: boolean;
  connected_at: string | null;
  last_sync_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface IntegrationCapabilityState {
  connected: boolean;
  configured: boolean;
  read_sync_ok: boolean;
  write_supported: boolean;
  verified: boolean;
  degraded: boolean;
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
  operating_state?: OperatingState;
  verification_result?: Record<string, unknown> | null;
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

export type OperatingState =
  | "drafted"
  | "gated"
  | "approved"
  | "executed"
  | "verified"
  | "learned";

export interface ChannelSnapshot {
  id: string;
  brand_id: string;
  channel: string;
  provider: string;
  snapshot_data: Record<string, unknown>;
  created_at: string;
}

export interface Content {
  id: string;
  brand_id: string;
  format: string;
  title: string | null;
  body: string | null;
  brief: Record<string, unknown> | null;
  gate_report: Record<string, unknown> | null;
  status: ContentStatus;
  skill: string | null;
  gateway_job_id: string | null;
  gateway_run_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  published_at: string | null;
}

export type ContentStatus = "draft" | "approved" | "published" | "rejected";

export interface AgentRun {
  id: string;
  brand_id: string;
  task_type: string;
  skill: string | null;
  trigger: string;
  status: "pending" | "running" | "completed" | "failed";
  input: Record<string, unknown> | null;
  output: Record<string, unknown> | null;
  error: string | null;
  risk_tier: "low" | "medium" | "high";
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export type RuntimeStatus = "online" | "offline" | "draining";

export interface AgentRuntime {
  id: string;
  daemon_id: string;
  brand_id: string | null;
  name: string;
  status: RuntimeStatus;
  last_heartbeat: string | null;
  updated_at: string;
}

export interface ActionTaskLineage {
  id: string;
  brand_id: string;
  action_id: string | null;
  agent_run_id: string | null;
  task_id: string | null;
  event_type: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  brand_id: string;
  role: "user" | "assistant" | "tool" | "system";
  content: string | null;
  tool_calls: Record<string, unknown> | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export type AutonomyMode = "supervised" | "balanced" | "autonomous";

// Provider mapping (mirrors gateway/adapters/pipedream/base.py)
export const PROVIDERS: ProviderConfig[] = [
  // Analytics
  {
    channel: "analytics", provider: "ga4", name: "Google Analytics", icon: "BarChart3", appSlug: "google_analytics",
    configRequired: { key: "ga4_property_id", label: "Property", type: "select", endpoint: "/api/analytics/properties", responseKey: "properties", optionLabel: "display_name", optionValue: "property_id" },
  },
  {
    channel: "analytics", provider: "gsc", name: "Google Search Console", icon: "Search", appSlug: "google_search_console",
    configRequired: { key: "gsc_site_url", label: "Site", type: "select", endpoint: "/api/analytics/gsc-sites", responseKey: "sites", optionLabel: "site_url", optionValue: "site_url" },
  },
  { channel: "analytics", provider: "gbp", name: "Google Business", icon: "MapPin", appSlug: "google_my_business" },
  { channel: "gbp", provider: "google_business_profile", name: "Google Business Profile", icon: "MapPin", appSlug: "google_my_business" },
  { channel: "calls", provider: "kaicalls", name: "KaiCalls", icon: "PhoneCall", appSlug: "kaicalls" },
  // Website
  {
    channel: "website", provider: "wordpress", name: "WordPress", icon: "Globe", appSlug: "wordpress_org",
    configRequired: { key: "wordpress_site_url", label: "Site URL", type: "text" },
  },
  {
    channel: "website", provider: "shopify", name: "Shopify", icon: "ShoppingBag", appSlug: "shopify",
    configRequired: { key: "shopify_store", label: "Store domain", type: "text" },
  },
  // Social
  {
    channel: "social", provider: "facebook", name: "Facebook", icon: "Facebook", appSlug: "facebook_pages",
    configRequired: { key: "facebook_page_id", label: "Page", type: "select", endpoint: "/api/sync/facebook/pages", responseKey: "pages", optionLabel: "name", optionValue: "id" },
  },
  {
    channel: "social", provider: "instagram", name: "Instagram", icon: "Instagram", appSlug: "facebook_pages",
    configRequired: { key: "instagram_account_id", label: "Account", type: "select", endpoint: "/api/sync/instagram/accounts", responseKey: "accounts", optionLabel: "name", optionValue: "id" },
  },
  {
    channel: "social", provider: "linkedin", name: "LinkedIn", icon: "Linkedin", appSlug: "linkedin",
    configRequired: { key: "linkedin_organization_id", label: "Organization", type: "select", endpoint: "/api/sync/linkedin/organizations", responseKey: "organizations", optionLabel: "name", optionValue: "id" },
  },
  { channel: "social", provider: "tiktok", name: "TikTok", icon: "Music", appSlug: "", comingSoon: true },
  { channel: "social", provider: "youtube", name: "YouTube", icon: "Youtube", appSlug: "youtube_data_api" },
  { channel: "social", provider: "twitter", name: "X / Twitter", icon: "Twitter", appSlug: "", comingSoon: true },
  { channel: "social", provider: "pinterest", name: "Pinterest", icon: "Pin", appSlug: "pinterest" },
  // Email
  { channel: "email", provider: "mailchimp", name: "Mailchimp", icon: "Mail", appSlug: "mailchimp" },
  { channel: "email", provider: "sendgrid", name: "SendGrid", icon: "Send", appSlug: "sendgrid" },
  { channel: "email", provider: "klaviyo", name: "Klaviyo", icon: "Zap", appSlug: "klaviyo" },
  { channel: "email", provider: "convertkit", name: "ConvertKit", icon: "UserCheck", appSlug: "convertkit" },
  { channel: "email", provider: "activecampaign", name: "ActiveCampaign", icon: "Send", appSlug: "activecampaign" },
  // Paid Media
  {
    channel: "paid_media", provider: "google_ads", name: "Google Ads", icon: "Megaphone", appSlug: "google_ads",
    configRequired: { key: "google_ads_customer_id", label: "Customer", type: "select", endpoint: "/api/sync/google-ads/customers", responseKey: "customers", optionLabel: "name", optionValue: "id" },
  },
  {
    channel: "paid_media", provider: "meta_ads", name: "Meta Ads", icon: "Target", appSlug: "facebook_graph_api",
    configRequired: { key: "meta_ads_account_id", label: "Ad Account", type: "select", endpoint: "/api/sync/meta-ads/accounts", responseKey: "accounts", optionLabel: "name", optionValue: "id" },
  },
  // CRM
  { channel: "crm", provider: "hubspot", name: "HubSpot", icon: "UserCheck", appSlug: "hubspot" },
  // Notifications
  { channel: "notifications", provider: "slack", name: "Slack", icon: "MessageSquare", appSlug: "slack_v2" },
  // Payments
  {
    channel: "payments", provider: "stripe", name: "Stripe", icon: "CreditCard", appSlug: "stripe",
    configRequired: { key: "stripe_account_id", label: "Account ID", type: "text" },
  },
  // Scheduling
  { channel: "scheduling", provider: "calendly", name: "Calendly", icon: "Calendar", appSlug: "calendly_v2" },
  // Content
  { channel: "content", provider: "notion", name: "Notion", icon: "BookOpen", appSlug: "notion" },
  { channel: "content", provider: "airtable", name: "Airtable", icon: "Table2", appSlug: "airtable_oauth" },
  { channel: "content", provider: "google_sheets", name: "Google Sheets", icon: "Table2", appSlug: "google_sheets" },
  // Website (additional)
  { channel: "website", provider: "webflow", name: "Webflow", icon: "Layout", appSlug: "webflow" },
  { channel: "website", provider: "squarespace", name: "Squarespace", icon: "SquareCode", appSlug: "squarespace" },
];

export interface ProviderConfigRequired {
  key: string;           // e.g. "ga4_property_id"
  label: string;         // e.g. "GA4 Property"
  type: "select" | "text";
  endpoint?: string;     // API to fetch options, e.g. "/api/analytics/properties"
  responseKey?: string;  // key in response containing the array
  optionLabel?: string;  // which field to display
  optionValue?: string;  // which field is the value
}

export interface ProviderConfig {
  channel: string;
  provider: string;
  name: string;
  icon: string;
  appSlug: string;
  configRequired?: ProviderConfigRequired;
  comingSoon?: boolean;
}

// Channel category groupings for the connect page
export const CHANNEL_CATEGORIES: Record<string, string[]> = {
  Analytics: ["analytics"],
  Website: ["website"],
  "GBP & Reviews": ["gbp"],
  Calls: ["calls"],
  Social: ["social"],
  Email: ["email"],
  "Paid Media": ["paid_media"],
  CRM: ["crm"],
  Content: ["content"],
  Payments: ["payments"],
  Scheduling: ["scheduling"],
  Notifications: ["notifications"],
};
