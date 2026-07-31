alter table public.social_posts add column if not exists action_id text;
alter table public.social_provider_receipts add column if not exists action_id text;

create unique index if not exists idx_social_receipts_post_provider
  on public.social_provider_receipts(post_id, provider);
create index if not exists idx_social_posts_action_id on public.social_posts(action_id);
