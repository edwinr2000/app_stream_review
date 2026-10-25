create table if not exists public.app_access_users (
    email text primary key,
    display_name text not null,
    password_hash text not null,
    role text not null check (role in ('SUPER_ADMIN', 'USER')),
    module_ids text[] not null default '{}',
    active boolean not null default true,
    updated_at timestamptz not null default now()
);

alter table public.app_access_users enable row level security;
