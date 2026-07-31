const DEFAULT_BASE_URL = "https://api.outstand.so";

export type OutstandAccount = {
  id: string;
  network?: string;
  username?: string;
  nickname?: string;
  status?: string;
  [key: string]: unknown;
};

export type OutstandPost = {
  id: string;
  scheduledAt?: string | null;
  publishedAt?: string | null;
  socialAccounts?: Array<OutstandAccount & { platformPostId?: string; error?: string }>;
  [key: string]: unknown;
};

function config() {
  const apiKey = process.env.OUTSTAND_API_KEY;
  if (!apiKey) throw new Error("OUTSTAND_API_KEY is not configured");
  return { apiKey, baseUrl: (process.env.OUTSTAND_API_BASE_URL || DEFAULT_BASE_URL).replace(/\/$/, "") };
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { apiKey, baseUrl } = config();
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json", ...(init.headers || {}) },
    cache: "no-store",
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(`Outstand ${response.status}: ${JSON.stringify(payload)}`);
  return payload as T;
}

export async function listAccounts() {
  const payload = await request<{ data?: OutstandAccount[]; accounts?: OutstandAccount[] }>("/v1/social-accounts");
  return payload.data || payload.accounts || [];
}

export async function getPost(postId: string) {
  const payload = await request<{ post?: OutstandPost }>(`/v1/posts/${encodeURIComponent(postId)}`);
  if (!payload.post) throw new Error("Outstand response did not include a post");
  return payload.post;
}
