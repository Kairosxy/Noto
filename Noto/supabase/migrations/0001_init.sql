-- Noto v1 schema
create extension if not exists vector;
create extension if not exists pgcrypto;

create table if not exists notebooks (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  goal text default '',
  created_at timestamptz not null default now()
);

create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  notebook_id uuid not null references notebooks(id) on delete cascade,
  filename text not null,
  storage_path text not null,
  mime text,
  pages int,
  status text not null default 'parsing',
  created_at timestamptz not null default now()
);

create table if not exists chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references documents(id) on delete cascade,
  content text not null,
  page_num int,
  position int not null,
  embedding vector(1024),
  created_at timestamptz not null default now()
);
create index if not exists idx_chunks_doc on chunks(document_id);
create index if not exists idx_chunks_embedding on chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create table if not exists conversations (
  id uuid primary key default gen_random_uuid(),
  notebook_id uuid not null references notebooks(id) on delete cascade,
  title text,
  status text not null default 'active',
  started_at timestamptz not null default now(),
  closed_at timestamptz
);

create table if not exists messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references conversations(id) on delete cascade,
  role text not null,
  content text not null,
  citations jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_messages_conv on messages(conversation_id, created_at);

create table if not exists cards (
  id uuid primary key default gen_random_uuid(),
  notebook_id uuid not null references notebooks(id) on delete cascade,
  source_conversation_id uuid references conversations(id) on delete set null,
  question text not null,
  answer text not null,
  due_at timestamptz not null default now(),
  ease int not null default 0,
  reps int not null default 0
);
create index if not exists idx_cards_due on cards(notebook_id, due_at);

create table if not exists reviews (
  id uuid primary key default gen_random_uuid(),
  card_id uuid not null references cards(id) on delete cascade,
  rating text not null,
  reviewed_at timestamptz not null default now()
);

create table if not exists reports (
  id uuid primary key default gen_random_uuid(),
  notebook_id uuid not null references notebooks(id) on delete cascade,
  from_date date not null,
  to_date date not null,
  content text not null,
  generated_at timestamptz not null default now()
);

-- Storage bucket
insert into storage.buckets (id, name, public) values ('documents', 'documents', false)
on conflict (id) do nothing;

create or replace function match_chunks(
  p_notebook_id uuid,
  p_query vector(1024),
  p_k int default 5
) returns table (
  id uuid,
  document_id uuid,
  content text,
  page_num int,
  distance float
) language sql stable as $$
  select c.id, c.document_id, c.content, c.page_num,
         (c.embedding <=> p_query) as distance
  from chunks c
  join documents d on d.id = c.document_id
  where d.notebook_id = p_notebook_id
    and d.status = 'ready'
    and c.embedding is not null
  order by c.embedding <=> p_query
  limit p_k;
$$;
