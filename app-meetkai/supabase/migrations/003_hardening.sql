-- Schema hardening: auto-update triggers, unique constraints, check constraints

-- Auto-update updated_at on row modification
create or replace function update_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger brands_updated_at before update on public.brands
  for each row execute function update_updated_at();
create trigger integrations_updated_at before update on public.integrations
  for each row execute function update_updated_at();
create trigger actions_updated_at before update on public.actions
  for each row execute function update_updated_at();

-- Prevent duplicate integrations per brand+channel+provider
alter table public.integrations
  add constraint unique_brand_channel_provider
  unique (brand_id, channel, provider);

-- Restrict approval_state to known values
alter table public.actions
  add constraint valid_approval_state
  check (approval_state in ('pending', 'approved', 'rejected', 'auto_approved', 'held'));

-- Restrict execution_state to known values
alter table public.actions
  add constraint valid_execution_state
  check (execution_state in ('pending', 'executing', 'completed', 'failed', 'rolled_back'));

-- Restrict integration status to known values
alter table public.integrations
  add constraint valid_status
  check (status in ('pending_auth', 'connected', 'degraded', 'disconnected', 'error'));
