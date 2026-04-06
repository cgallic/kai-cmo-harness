export interface GatewayResponse<T = unknown> {
  success: boolean;
  data: T;
  error: string | null;
  timestamp: string;
}

export interface AsyncJobResponse {
  job_id: string;
  run_id?: string;
  status: "pending" | "queued";
  message: string;
}

export interface JobInfo {
  job_id: string;
  status: "pending" | "running" | "completed" | "failed";
  command: string;
  result: unknown;
  error: string | null;
  created_at: string;
  completed_at: string | null;
  artifacts: ArtifactInfo[];
}

export interface ArtifactInfo {
  artifact_id: string;
  artifact_type: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface ProposalRequest {
  brand_id: string;
  channel: string;
  action_type: string;
  intent: string;
  proposed_changes: Record<string, unknown>;
  source_run_id?: string;
  metadata?: Record<string, unknown>;
}

export interface ProposalResponse {
  action_id: string;
  risk_tier: string;
  policy_result: Record<string, unknown>;
  approval_state: string;
  auto_eligible: boolean;
}

export interface DashboardResponse {
  pending_count: number;
  recent_actions: unknown[];
  active_integrations: unknown[];
  channel_summary: Record<string, unknown>;
}

export interface AgentStatus {
  running: boolean;
  paused: boolean;
  tasks: unknown[];
  last_execution: string | null;
}

export interface AgentExecution {
  id: string;
  task_type: string;
  client: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  result: unknown;
  error: string | null;
}

export interface RunInfo {
  run_id: string;
  workflow: string;
  brand_id: string;
  status: string;
  surface: string;
  created_at: string;
  completed_at: string | null;
  artifacts: ArtifactInfo[];
}
