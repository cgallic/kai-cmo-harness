import { gateway } from "./client";
import type { AsyncJobResponse, GatewayResponse, JobInfo } from "./types";

function unwrapGatewayResponse<T>(payload: T | GatewayResponse<T>): T {
  if (
    payload &&
    typeof payload === "object" &&
    "success" in payload &&
    "data" in payload
  ) {
    const wrapped = payload as GatewayResponse<T>;
    if (!wrapped.success) {
      throw new Error(wrapped.error || "Gateway request failed");
    }
    return wrapped.data;
  }
  return payload as T;
}

export async function generateContent(req: {
  format: string;
  site: string;
  keyword: string;
  persona?: string;
  dry_run?: boolean;
  skip_gates?: boolean;
  brand_id?: string;
}): Promise<AsyncJobResponse> {
  return gateway<AsyncJobResponse>("/generate", {
    method: "POST",
    body: { ...req, surface: "remote" },
    timeout: 60000,
  });
}

export async function getGenerateJob(jobId: string): Promise<JobInfo> {
  const payload = await gateway<JobInfo | GatewayResponse<JobInfo>>(`/jobs/${jobId}`);
  return unwrapGatewayResponse(payload);
}

export async function getJobArtifacts(jobId: string) {
  const payload = await gateway<
    { artifacts: unknown[] } | GatewayResponse<{ artifacts: unknown[] }>
  >(`/jobs/${jobId}/artifacts`);
  return unwrapGatewayResponse(payload);
}
