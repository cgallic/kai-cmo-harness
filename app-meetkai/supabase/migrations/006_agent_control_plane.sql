-- 006_agent_control_plane.sql: tenant-safe agent control-plane state and lineage

alter table public.runtimes
  add column if not exists brand_id uuid references public.brands(id) on delete cascade;

create table public.action_task_lineage (
  id uuid primary key default uuid_generate_v4(),
  brand_id uuid not null references public.brands(id) on delete cascade,
  action_id uuid references public.actions(id) on delete set null,
  agent_run_id uuid references public.agent_runs(id) on delete set null,
  task_id text,
  event_type text not null,
  payload jsonb not null default '{}',
  created_at timestamptz not null default now(),
  check (action_id is not null or agent_run_id is not null or task_id is not null)
);

create index idx_runtimes_brand on public.runtimes(brand_id);
create index idx_lineage_brand_created on public.action_task_lineage(brand_id, created_at desc);
create index idx_lineage_action on public.action_task_lineage(action_id, created_at desc);
create index idx_lineage_agent_run on public.action_task_lineage(agent_run_id, created_at desc);

alter table public.action_task_lineage enable row level security;

create policy "action_task_lineage_select" on public.action_task_lineage
  for select using (brand_id in (select id from public.brands where user_id = auth.uid()));

alter publication supabase_realtime add table public.action_task_lineage;
