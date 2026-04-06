import { gateway } from "./client";
import type { AsyncJobResponse, JobInfo } from "./types";

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
  return gateway<JobInfo>(`/jobs/${jobId}`);
}

export async function getJobArtifacts(jobId: string) {
  return gateway<{ artifacts: unknown[] }>(`/jobs/${jobId}/artifacts`);
}
