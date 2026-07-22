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
  run_id?: string;
  status: "pending" | "running" | "completed" | "failed";
  run_status?: string | null;
  approval_state?: string | null;
  command: string;
  client?: string | null;
  workflow?: string | null;
  brand_id?: string | null;
  surface?: string | null;
  module_set?: string[];
  inputs?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  runtime_metadata?: Record<string, unknown>;
  result: unknown;
  run_outputs?: Record<string, unknown>;
  error: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at: string | null;
  lineage_run_ids?: string[];
  artifact_ids?: string[];
  artifact_count?: number;
  artifacts?: ArtifactInfo[];
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

export interface Bottleneck {
  brand_id: string;
  brand_name: string;
  lifecycle: string;
  health: string;
  blocked_gate: string;
  owner: string;
  next_action: string;
  close_condition: string;
  evidence_refs: string[];
  summary?: string;
  proof_state?: string;
}

export interface ImplementationCoach {
  state: string;
  message: string;
  next_action: string;
  close_condition: string;
  evidence_refs: string[];
}

export interface PortfolioBrand {
  brand_id: string;
  brand_name: string;
  lifecycle: string;
  health: string;
  blocked_gate: string;
  owner: string;
  next_action: string;
  close_condition: string;
  evidence_refs: string[];
}

export interface AutopilotCommandCenterResponse {
  primary_bottleneck: Bottleneck | null;
  coach: ImplementationCoach;
  portfolio: PortfolioBrand[];
  timestamp: string;
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
