const GATEWAY_URL = process.env.GATEWAY_URL || "http://89.167.60.171:10002";
const GATEWAY_API_KEY = process.env.GATEWAY_API_KEY || "";

export class GatewayError extends Error {
  constructor(
    public status: number,
    public body: unknown,
    message?: string,
  ) {
    super(message || `Gateway error ${status}`);
    this.name = "GatewayError";
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "DELETE";
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined>;
  timeout?: number;
}

export async function gateway<T = unknown>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, params, timeout = 30000 } = options;

  const url = new URL(path, GATEWAY_URL);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);

  try {
    const res = await fetch(url.toString(), {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(GATEWAY_API_KEY ? { "X-API-Key": GATEWAY_API_KEY } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    const data = await res.json();

    if (!res.ok) {
      throw new GatewayError(res.status, data, data?.error || `Gateway ${res.status}`);
    }

    return data as T;
  } finally {
    clearTimeout(timer);
  }
}
