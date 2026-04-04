-- Enable Realtime on integrations table for live status updates
alter publication supabase_realtime add table public.integrations;
