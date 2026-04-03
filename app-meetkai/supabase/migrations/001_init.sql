-- MeetKai Dashboard Schema
-- Run this against your Supabase project

create extension if not exists "uuid-ossp";

-- Brands (one per business)
create table public.brands (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  url text,
  description text,
  archetype text default 'local_service',
  active_channels text[] default '{}',
  metadata jsonb default '{}',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Audit results (from MiKai engine)
create table public.audits (
  id uuid primary key default uuid_generate_v4(),
  brand_id uuid not null references public.brands(id) on delete cascade,
  overall_score numeric,
  category_scores jsonb default '{}',
  findings jsonb default '[]',
  metadata jsonb default '{}',
  created_at timestamptz default now()
);

-- Connected integrations (Pipedream accounts)
create table public.integrations (
  id uuid primary key default uuid_generate_v4(),
  brand_id uuid not null references public.brands(id) on delete cascade,
  channel text not null,
  provider text not null,
  status text default 'pending_auth',
  connected_account_id text,
  capabilities text[] default '{}',
  config jsonb default '{}',
  metadata jsonb default '{}',
  connected_at timestamptz,
  last_sync_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Action proposals (AI-generated marketing actions)
create table public.actions (
  id uuid primary key default uuid_generate_v4(),
  brand_id uuid not null references public.brands(id) on delete cascade,
  action_type text not null,
  channel text not null,
  intent text,
  approval_state text default 'pending',
  execution_state text default 'pending',
  risk_tier text default 'medium',
  proposed_changes jsonb default '{}',
  result_summary jsonb,
  metadata jsonb default '{}',
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  executed_at timestamptz
);

-- Channel data snapshots (analytics, metrics)
create table public.channel_snapshots (
  id uuid primary key default uuid_generate_v4(),
  brand_id uuid not null references public.brands(id) on delete cascade,
  channel text not null,
  provider text not null,
  snapshot_data jsonb default '{}',
  created_at timestamptz default now()
);

-- Enable RLS on all tables
alter table public.brands enable row level security;
alter table public.audits enable row level security;
alter table public.integrations enable row level security;
alter table public.actions enable row level security;
alter table public.channel_snapshots enable row level security;

-- Brands: users see/edit their own
create policy "brands_select" on public.brands
  for select using (auth.uid() = user_id);
create policy "brands_insert" on public.brands
  for insert with check (auth.uid() = user_id);
create policy "brands_update" on public.brands
  for update using (auth.uid() = user_id);

-- Child tables: cascade through brand ownership
create policy "audits_select" on public.audits
  for select using (brand_id in (select id from public.brands where user_id = auth.uid()));

create policy "integrations_select" on public.integrations
  for select using (brand_id in (select id from public.brands where user_id = auth.uid()));
create policy "integrations_insert" on public.integrations
  for insert with check (brand_id in (select id from public.brands where user_id = auth.uid()));
create policy "integrations_update" on public.integrations
  for update using (brand_id in (select id from public.brands where user_id = auth.uid()));

create policy "actions_select" on public.actions
  for select using (brand_id in (select id from public.brands where user_id = auth.uid()));
create policy "actions_update" on public.actions
  for update using (brand_id in (select id from public.brands where user_id = auth.uid()));

create policy "snapshots_select" on public.channel_snapshots
  for select using (brand_id in (select id from public.brands where user_id = auth.uid()));

-- Enable Realtime on actions for live status updates
alter publication supabase_realtime add table public.actions;

-- Indexes
create index idx_brands_user_id on public.brands(user_id);
create index idx_audits_brand_id on public.audits(brand_id);
create index idx_integrations_brand_id on public.integrations(brand_id);
create index idx_integrations_status on public.integrations(status);
create index idx_actions_brand_id on public.actions(brand_id);
create index idx_actions_approval_state on public.actions(approval_state);
create index idx_actions_execution_state on public.actions(execution_state);
create index idx_snapshots_brand_id on public.channel_snapshots(brand_id);
create index idx_snapshots_channel on public.channel_snapshots(brand_id, channel);
