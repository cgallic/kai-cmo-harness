export type SocialPostStatus = "draft" | "approved" | "scheduled" | "publishing" | "published" | "failed" | "cancelled";
export type SocialMediaType = "image" | "video";
export type SocialReceiptStatus = "pending" | "publishing" | "published" | "failed";

export interface SocialPostMedia { id: string; post_id: string; media_url: string; media_type: SocialMediaType; sort_order: number; metadata: Record<string, unknown>; created_at: string; }
export interface SocialProviderReceipt { id: string; post_id: string; brand_id: string; provider: string; status: SocialReceiptStatus; provider_post_id: string | null; provider_url: string | null; error: string | null; response: Record<string, unknown>; published_at: string | null; created_at: string; updated_at: string; }
export interface SocialPost { id: string; brand_id: string; status: SocialPostStatus; caption: string; platforms: string[]; scheduled_at: string | null; approved_at: string | null; approved_by: string | null; metadata: Record<string, unknown>; created_at: string; updated_at: string; media?: SocialPostMedia[]; receipts?: SocialProviderReceipt[]; }
