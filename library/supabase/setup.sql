-- Run once in Supabase → SQL Editor. One row per book; each person can only
-- read and write their own rows.
create table if not exists public.books (
    id text primary key,
    user_id uuid not null default auth.uid() references auth.users on delete cascade,
    data jsonb not null,
    updated bigint not null default 0,
    deleted boolean not null default false
);

alter table public.books enable row level security;

create policy "People manage their own books"
    on public.books for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);
