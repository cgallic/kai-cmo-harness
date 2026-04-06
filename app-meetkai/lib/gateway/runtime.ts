import { gateway } from "./client";
import type { RunInfo } from "./types";

export async function listRuns(filters?: {
  brand_id?: string;
  workflow?: string;
  status?: string;
  limit?: number;
}) {
  return gateway<{ runs: RunInfo[] }>("/runtime/runs", {
    params: filters as Record<string, string | number>,
  });
}

export async function getRun(runId: string): Promise<RunInfo> {
  return gateway<RunInfo>(`/runtime/runs/${runId}`);
}

export async function approveRun(runId: string, note?: string) {
  return gateway(`/runtime/runs/${runId}/approve`, {
    method: "POST",
    body: { note },
  });
}

export async function rejectRun(runId: string, note?: string) {
  return gateway(`/runtime/runs/${runId}/reject`, {
    method: "POST",
    body: { note },
  });
}

export async function listApprovals(filters?: {
  brand_id?: string;
  workflow?: string;
  limit?: number;
}) {
  return gateway<{ approvals: RunInfo[] }>("/runtime/approvals", {
    params: filters as Record<string, string | number>,
  });
}

export async function listArtifacts(filters?: {
  brand_id?: string;
  artifact_type?: string;
  limit?: number;
}) {
  return gateway<{ artifacts: unknown[] }>("/runtime/artifacts", {
    params: filters as Record<string, string | number>,
  });
}
