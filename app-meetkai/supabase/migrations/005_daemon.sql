-- 005_daemon.sql: Daemon infrastructure — runtimes, agent messages, schedules

-- ============================================================================
-- Runtimes: registered daemon instances
-- ============================================================================

create table public.runtimes (
  id uuid primary key default uuid_generate_v4(),
  daemon_id text not null unique,
  name text not null,
  host_info jsonb default '{}',
  status text not null default 'offline',
  last_heartbeat timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.runtimes
  add constraint valid_runtime_status
  check (status in ('online', 'offline', 'draining'));

create trigger runtimes_updated_at before update on public.runtimes
  for each row execute function update_updated_at();

-- ============================================================================
-- Agent messages: execution transcript (streamed in realtime)
-- ============================================================================

create table public.agent_messages (
  id uuid primary key default uuid_generate_v4(),
  run_id uuid not null references public.agent_runs(id) on delete cascade,
  brand_id uuid not null references public.brands(id) on delete cascade,
  seq integer not null,
  msg_type text not null,
  content text,
  metadata jsonb default '{}',
  created_at timestamptz default now()
);

alter table public.agent_messages
  add constraint valid_msg_type
  check (msg_type in ('text', 'tool_use', 'tool_result', 'thinking', 'error', 'status'));

create index idx_agent_messages_run on public.agent_messages(run_id, seq);
create index idx_agent_messages_brand on public.agent_messages(brand_id);

-- ============================================================================
-- Schedules: recurring task definitions
-- ============================================================================

create table public.schedules (
  id uuid primary key default uuid_generate_v4(),
  brand_id uuid not null references public.brands(id) on delete cascade,
  name text not null,
  cron_expr text not null,
  skill text not null,
  task_type text not null,
  input jsonb default '{}',
  enabled boolean default true,
  last_run_at timestamptz,
  next_run_at timestamptz,
  created_at timestamptz default now()
);

create index idx_schedules_brand on public.schedules(brand_id);
create index idx_schedules_next_run on public.schedules(next_run_at) where enabled = true;

-- ============================================================================
-- Extend agent_runs with daemon fields
-- ============================================================================

alter table public.agent_runs add column if not exists runtime_id uuid references public.runtimes(id);
alter table public.agent_runs add column if not exists session_id text;
alter table public.agent_runs add column if not exists claimed_at timestamptz;
alter table public.agent_runs add column if not exists work_dir text;
alter table public.agent_runs add column if not exists schedule_id uuid references public.schedules(id);
alter table public.agent_runs add column if not exists progress jsonb default '{}';

create index idx_agent_runs_claimed on public.agent_runs(claimed_at) where claimed_at is null;

-- ============================================================================
-- Atomic claim lock function (prevents race conditions)
-- ============================================================================

create or replace function public.claim_agent_task(
  p_runtime_id uuid
)
returns uuid as $$
declare
  v_task_id uuid;
begin
  select id into v_task_id
  from public.agent_runs
  where status = 'pending'
    and claimed_at is null
  order by created_at asc
  limit 1
  for update skip locked;

  if v_task_id is null then
    return null;
  end if;

  update public.agent_runs
  set runtime_id = p_runtime_id,
      claimed_at = now(),
      status = 'running',
      started_at = now()
  where id = v_task_id;

  return v_task_id;
end;
$$ language plpgsql;

-- ============================================================================
-- RLS policies
-- ============================================================================

alter table public.runtimes enable row level security;
alter table public.agent_messages enable row level security;
alter table public.schedules enable row level security;

-- Runtimes: service role only (daemon writes, no user access needed)
-- No user-facing RLS policies — runtimes managed by gateway with service_role key

-- Agent messages: users can read messages for their brands
create policy "agent_messages_select" on public.agent_messages
  for select using (brand_id in (select id from public.brands where user_id = auth.uid()));

-- Allow service_role inserts (daemon writes via gateway)
-- No insert policy for anon/authenticated — daemon uses service_role key

-- Schedules: users can manage schedules for their brands
create policy "schedules_select" on public.schedules
  for select using (brand_id in (select id from public.brands where user_id = auth.uid()));
create policy "schedules_insert" on public.schedules
  for insert with check (brand_id in (select id from public.brands where user_id = auth.uid()));
create policy "schedules_update" on public.schedules
  for update using (brand_id in (select id from public.brands where user_id = auth.uid()));
create policy "schedules_delete" on public.schedules
  for delete using (brand_id in (select id from public.brands where user_id = auth.uid()));

-- ============================================================================
-- Enable Realtime
-- ============================================================================

alter publication supabase_realtime add table public.agent_messages;
alter publication supabase_realtime add table public.runtimes;
alter publication supabase_realtime add table public.schedules;
