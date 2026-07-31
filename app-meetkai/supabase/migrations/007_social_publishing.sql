-- Tenant-scoped social publishing records and provider receipts.
create table public.social_posts (
  id uuid primary key default uuid_generate_v4(),
  brand_id uuid not null references public.brands(id) on delete cascade,
  status text not null default 'draft',
  caption text not null,
  platforms text[] not null default '{}',
  scheduled_at timestamptz,
  approved_at timestamptz,
  approved_by uuid references auth.users(id),
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint social_posts_status_check check (status in ('draft', 'approved', 'scheduled', 'publishing', 'published', 'failed', 'cancelled'))
);

create table public.social_post_media (
  id uuid primary key default uuid_generate_v4(),
  post_id uuid not null references public.social_posts(id) on delete cascade,
  media_url text not null,
  media_type text not null default 'image',
  sort_order integer not null default 0,
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now(),
  constraint social_post_media_type_check check (media_type in ('image', 'video'))
);

create table public.social_provider_receipts (
  id uuid primary key default uuid_generate_v4(),
  post_id uuid not null references public.social_posts(id) on delete cascade,
  brand_id uuid not null references public.brands(id) on delete cascade,
  provider text not null,
  status text not null default 'pending',
  provider_post_id text,
  provider_url text,
  error text,
  response jsonb not null default '{}',
  published_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint social_provider_receipts_status_check check (status in ('pending', 'publishing', 'published', 'failed'))
);

alter table public.social_posts enable row level security;
alter table public.social_post_media enable row level security;
alter table public.social_provider_receipts enable row level security;

create policy "social_posts_select" on public.social_posts for select
  using (brand_id in (select id from public.brands where user_id = auth.uid()));
create policy "social_posts_insert" on public.social_posts for insert
  with check (brand_id in (select id from public.brands where user_id = auth.uid()));
create policy "social_posts_update" on public.social_posts for update
  using (brand_id in (select id from public.brands where user_id = auth.uid()));

create policy "social_post_media_select" on public.social_post_media for select
  using (post_id in (select id from public.social_posts where brand_id in (select id from public.brands where user_id = auth.uid())));
create policy "social_post_media_insert" on public.social_post_media for insert
  with check (post_id in (select id from public.social_posts where brand_id in (select id from public.brands where user_id = auth.uid())));

create policy "social_provider_receipts_select" on public.social_provider_receipts for select
  using (brand_id in (select id from public.brands where user_id = auth.uid()));

create index idx_social_posts_brand_status on public.social_posts(brand_id, status, created_at desc);
create index idx_social_post_media_post on public.social_post_media(post_id, sort_order);
create index idx_social_provider_receipts_post on public.social_provider_receipts(post_id, provider);

create trigger social_posts_updated_at before update on public.social_posts
  for each row execute function update_updated_at();
create trigger social_provider_receipts_updated_at before update on public.social_provider_receipts
  for each row execute function update_updated_at();

alter publication supabase_realtime add table public.social_posts;
alter publication supabase_realtime add table public.social_provider_receipts;
