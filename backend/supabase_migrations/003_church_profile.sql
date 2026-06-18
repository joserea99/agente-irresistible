-- 003_church_profile.sql
-- Singleton "church memory": context about THIS church that the agent injects
-- into every response so directors know who they're advising.
-- Deployment model is one instance per church, so a single row (id = 1) is used.

create table if not exists public.church_profile (
    id               int primary key default 1,
    church_name      text,
    city             text,
    country          text,
    size             text,          -- e.g. "120 asistentes promedio"
    service_schedule text,          -- e.g. "Domingos 10am y 12pm"
    current_series   text,          -- current sermon/teaching series
    vision           text,          -- the church's vision / "the win"
    notes            text,          -- any extra context the team wants the agent to remember
    updated_at       timestamptz default now(),
    constraint church_profile_single_row check (id = 1)
);

-- Seed the singleton row so upserts always target id = 1.
insert into public.church_profile (id)
values (1)
on conflict (id) do nothing;

-- RLS: readable by any authenticated user; writes go through the service role
-- (backend admin endpoint), consistent with the other tables in 002.
alter table public.church_profile enable row level security;

drop policy if exists "church_profile_read" on public.church_profile;
create policy "church_profile_read"
    on public.church_profile
    for select
    to authenticated
    using (true);
