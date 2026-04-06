import { gateway } from "./client";

export async function runAudit(businessId: string, scope = "full") {
  return gateway<Record<string, unknown>>(`/kai-operator/audit/${businessId}`, {
    method: "GET",
    params: { scope },
    timeout: 120000,
  });
}
