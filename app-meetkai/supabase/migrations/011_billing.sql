-- MeetKai plan billing (Stripe subscriptions).
-- One row per user. Written only by the Stripe webhook (service role);
-- users can read their own row. NOT applied automatically.

create table if not exists public.billing_accounts (
  user_id uuid primary key references auth.users(id) on delete cascade,
  stripe_customer_id text unique,
  stripe_subscription_id text,
  plan text check (plan in ('starter', 'growth', 'scale')),
  status text,
  current_period_end timestamptz,
  last_event_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.billing_accounts enable row level security;

create policy "billing_accounts_select_own" on public.billing_accounts
  for select using (auth.uid() = user_id);

-- No insert/update/delete policies: only the service role (webhook) writes.
