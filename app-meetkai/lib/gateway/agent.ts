import { gateway } from "./client";
import type { AgentStatus, AgentExecution } from "./types";

export async function getAgentStatus(): Promise<AgentStatus> {
  return gateway<AgentStatus>("/agent/status");
}

export async function getRecentExecutions(limit = 20): Promise<{ executions: AgentExecution[] }> {
  return gateway<{ executions: AgentExecution[] }>("/agent/executions", {
    params: { limit },
  });
}

export async function getUpcomingTasks(limit = 10) {
  return gateway<{ tasks: unknown[] }>("/agent/upcoming", {
    params: { limit },
  });
}

export async function runTask(taskType: string) {
  return gateway("/agent/run/" + taskType, {
    method: "POST",
    timeout: 120000,
  });
}
