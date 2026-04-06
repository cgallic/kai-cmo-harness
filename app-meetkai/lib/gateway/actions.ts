import { gateway } from "./client";
import type { ProposalRequest, ProposalResponse, DashboardResponse } from "./types";

export async function propose(req: ProposalRequest): Promise<ProposalResponse> {
  return gateway<ProposalResponse>("/ops/propose", {
    method: "POST",
    body: req,
  });
}

export async function listProposals(brandId: string, limit = 20) {
  return gateway<{ proposals: unknown[]; count: number }>("/ops/proposals", {
    params: { brand_id: brandId, limit },
  });
}

export async function approveProposal(actionId: string, note?: string) {
  return gateway(`/ops/proposals/${actionId}/approve`, {
    method: "POST",
    body: { note },
  });
}

export async function rejectProposal(actionId: string, note?: string) {
  return gateway(`/ops/proposals/${actionId}/reject`, {
    method: "POST",
    body: { note },
  });
}

export async function listActions(brandId: string, filters?: {
  channel?: string;
  approval_state?: string;
  execution_state?: string;
  limit?: number;
}) {
  return gateway<{ actions: unknown[] }>("/ops/actions", {
    params: { brand_id: brandId, ...filters },
  });
}

export async function getDashboard(brandId?: string): Promise<DashboardResponse> {
  return gateway<DashboardResponse>("/ops/dashboard", {
    params: brandId ? { brand_id: brandId } : {},
  });
}
