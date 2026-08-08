-- 010: retention for the two tables that grow without bound.
--
-- Nothing in this schema has ever deleted anything. Grep across every migration
-- and every cron route for "delete from", pg_cron, retention, or vacuum returns
-- nothing. Two tables accumulate forever:
--
--   channel_snapshots  -- one row per channel per sync, snapshot_data jsonb.
--                         The sync-all cron runs daily across ~30 connectors.
--   agent_messages     -- one row per message of every agent transcript, with
--                         full content text plus metadata jsonb.
--
-- IMPORTANT -- this migration does not delete anything. It only installs the
-- functions. A bulk DELETE against an instance that is already disk-pressured
-- generates WAL and dead tuples faster than autovacuum reclaims them, so it
-- makes the problem worse before better. The intended order is:
--
--   1. Raise compute/disk so there is headroom.
--   2. Call the prune functions repeatedly in small batches (they are designed
--      to be called in a loop and report what they removed).
--   3. VACUUM (or VACUUM FULL, which takes an exclusive lock) during a quiet
--      window to return the space to the filesystem.
--
-- Deleting rows alone will not shrink the database on disk. Step 3 is the one
-- that actually frees space.

-- ---------------------------------------------------------------------------
-- channel_snapshots
-- ---------------------------------------------------------------------------
-- A snapshot table is not a log: the newest row per (brand, channel, provider)
-- IS the current known state of that channel. Deleting purely by age would
-- silently erase the latest reading for any channel that stopped syncing, so
-- the most recent row per series is always kept regardless of age.

create or replace function public.prune_channel_snapshots(
  p_keep_days integer default 90,
  p_batch_size integer default 5000
)
returns integer as $$
declare
  v_deleted integer;
begin
  with candidates as (
    select id
    from (
      select
        id,
        created_at,
        row_number() over (
          partition by brand_id, channel, provider
          order by created_at desc
        ) as recency
      from public.channel_snapshots
    ) ranked
    where recency > 1                                   -- never the latest
      and created_at < now() - make_interval(days => p_keep_days)
    limit p_batch_size
  )
  delete from public.channel_snapshots s
  using candidates c
  where s.id = c.id;

  get diagnostics v_deleted = row_count;
  return v_deleted;
end;
$$ language plpgsql security definer set search_path = public, pg_temp;

comment on function public.prune_channel_snapshots(integer, integer) is
  'Deletes up to p_batch_size channel_snapshots older than p_keep_days, always '
  'preserving the most recent row per (brand_id, channel, provider). Returns '
  'the number deleted; call in a loop until it returns 0.';

-- ---------------------------------------------------------------------------
-- agent_messages
-- ---------------------------------------------------------------------------
-- Pure transcript log. agent_runs.output retains the result of each run, so
-- pruning messages loses the step-by-step trace, not the deliverable. Rows also
-- cascade when their agent_run is deleted.

create or replace function public.prune_agent_messages(
  p_keep_days integer default 30,
  p_batch_size integer default 5000
)
returns integer as $$
declare
  v_deleted integer;
begin
  with candidates as (
    select id
    from public.agent_messages
    where created_at < now() - make_interval(days => p_keep_days)
    limit p_batch_size
  )
  delete from public.agent_messages m
  using candidates c
  where m.id = c.id;

  get diagnostics v_deleted = row_count;
  return v_deleted;
end;
$$ language plpgsql security definer set search_path = public, pg_temp;

comment on function public.prune_agent_messages(integer, integer) is
  'Deletes up to p_batch_size agent_messages older than p_keep_days. Returns '
  'the number deleted; call in a loop until it returns 0.';

-- Both functions are SECURITY DEFINER, so the default EXECUTE grant to PUBLIC
-- has to go -- otherwise any authenticated user could call them.
revoke execute on function public.prune_channel_snapshots(integer, integer) from public;
revoke execute on function public.prune_channel_snapshots(integer, integer) from anon;
revoke execute on function public.prune_channel_snapshots(integer, integer) from authenticated;
grant  execute on function public.prune_channel_snapshots(integer, integer) to service_role;

revoke execute on function public.prune_agent_messages(integer, integer) from public;
revoke execute on function public.prune_agent_messages(integer, integer) from anon;
revoke execute on function public.prune_agent_messages(integer, integer) from authenticated;
grant  execute on function public.prune_agent_messages(integer, integer) to service_role;

-- Age-ordered lookups are what both functions scan on.
create index if not exists channel_snapshots_created_at_idx
  on public.channel_snapshots (created_at);

create index if not exists agent_messages_created_at_idx
  on public.agent_messages (created_at);

-- ---------------------------------------------------------------------------
-- Finding out what is actually big, before deleting anything
-- ---------------------------------------------------------------------------
-- Run this first. If channel_snapshots is not near the top, the disk problem is
-- somewhere else and pruning it will not help.
--
--   select relname,
--          pg_size_pretty(pg_total_relation_size(c.oid)) as total,
--          n_live_tup
--   from pg_class c
--   join pg_stat_user_tables s on s.relid = c.oid
--   where c.relkind = 'r'
--   order by pg_total_relation_size(c.oid) desc
--   limit 15;
--
-- Then prune in batches, e.g.:
--
--   select public.prune_channel_snapshots(90, 5000);   -- repeat until it returns 0
--   select public.prune_agent_messages(30, 5000);      -- repeat until it returns 0
--
-- Then reclaim. VACUUM FULL takes an ACCESS EXCLUSIVE lock and needs free space
-- equal to the table size, so on a small instance prefer pg_repack, or vacuum
-- one table at a time during a quiet window:
--
--   vacuum full analyze public.channel_snapshots;
