-- 009: enforce tenant scope inside claim_agent_task, in SQL.
--
-- Migration 006 added runtimes.brand_id ("tenant-safe agent control-plane
-- state") and the read paths honour it -- app/api/agent/status/route.ts filters
-- on it. But claim_agent_task never consulted it. Its predicate was:
--
--     where status = 'pending' and claimed_at is null
--     order by created_at asc
--
-- No brand filter of any kind. Every daemon holding the service_role key
-- competed for one global FIFO queue, so any runtime could claim, execute, and
-- write back any tenant's task. The column to fix it already existed; only the
-- enforcement was missing.
--
-- Rule now:
--   * runtimes.brand_id IS NULL  -> unscoped runtime, may claim any brand.
--     This preserves today's single-tenant behaviour, where nothing sets the
--     column, so existing deployments keep working after this migration.
--   * runtimes.brand_id IS SET   -> the runtime may claim only that brand.
--     Binding is enforced here, in the database, not in the Python caller.
--
-- Once more than one paying tenant exists, every runtime must be bound. An
-- unscoped runtime is a single-tenant convenience, not a multi-tenant design.
-- See the companion check in daemon/__main__.py, which refuses to start
-- unscoped when MEETKAI_REQUIRE_BRAND_SCOPE=true.

create or replace function public.claim_agent_task(
  p_runtime_id uuid
)
returns uuid as $$
declare
  v_task_id uuid;
  v_brand_id uuid;
  v_runtime_exists boolean;
begin
  -- The runtime must exist. Previously an unregistered (or bogus) runtime id
  -- reached the UPDATE and was only caught by the FK, after selection.
  select true, brand_id
    into v_runtime_exists, v_brand_id
  from public.runtimes
  where id = p_runtime_id;

  if not coalesce(v_runtime_exists, false) then
    raise exception 'unknown runtime %', p_runtime_id
      using errcode = 'foreign_key_violation';
  end if;

  select id into v_task_id
  from public.agent_runs
  where status = 'pending'
    and claimed_at is null
    -- NULL brand_id on the runtime means unscoped; otherwise it must match.
    and (v_brand_id is null or brand_id = v_brand_id)
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
$$ language plpgsql security definer set search_path = public, pg_temp;

-- The function was SECURITY INVOKER and, with no GRANT/REVOKE anywhere in this
-- schema, kept Postgres' default EXECUTE to PUBLIC -- reachable over PostgREST
-- by anon and authenticated. It is now SECURITY DEFINER (so the scope check
-- cannot be sidestepped by the caller's own privileges), which makes removing
-- that default grant mandatory rather than merely tidy.
revoke execute on function public.claim_agent_task(uuid) from public;
revoke execute on function public.claim_agent_task(uuid) from anon;
revoke execute on function public.claim_agent_task(uuid) from authenticated;
grant execute on function public.claim_agent_task(uuid) to service_role;

comment on function public.claim_agent_task(uuid) is
  'Claims the oldest pending agent_run the given runtime is permitted to run. '
  'A runtime with a non-null brand_id is restricted to that brand; a null '
  'brand_id is unscoped and may claim any. service_role only.';

-- Make the scoped claim path indexable rather than a full scan per poll (every
-- 3s per daemon).
create index if not exists agent_runs_pending_claim_idx
  on public.agent_runs (brand_id, created_at)
  where status = 'pending' and claimed_at is null;
