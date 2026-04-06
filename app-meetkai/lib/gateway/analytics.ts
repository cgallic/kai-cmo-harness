import { gateway } from "./client";

export async function getAnalyticsSummary(client: string) {
  return gateway<Record<string, unknown>>("/webhooks/analytics/summary", {
    method: "POST",
    body: { client },
  });
}

export async function getGscQueries(client: string) {
  return gateway<Record<string, unknown>>("/webhooks/analytics/gsc/queries", {
    method: "POST",
    body: { client },
  });
}
