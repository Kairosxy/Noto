-- v2 schema: skeleton distillation + card state + highlights

-- 1. Space-level skeleton (1 per notebook)
create table if not exists skeletons (
  id uuid primary key default gen_random_uuid(),
  notebook_id uuid not null references notebooks(id) on delete cascade,
  space_summary text,
  generated_at timestamptz not null default now(),
  status text not null default 'ready'
);
create unique index if not exists idx_skeletons_notebook on skeletons(notebook_id);

-- 2. Learning directions (0..6 per skeleton)
create table if not exists learning_directions (
  id uuid primary key default gen_random_uuid(),
  skeleton_id uuid not null references skeletons(id) on delete cascade,
  notebook_id uuid not null references notebooks(id) on delete cascade,
  position int not null,
  title text not null,
  description text,
  estimated_minutes int
);
create index if not exists idx_directions_skeleton on learning_directions(skeleton_id, position);

-- 3. Skeleton nodes (claims / concepts / questions / pitfalls)
create table if not exists skeleton_nodes (
  id uuid primary key default gen_random_uuid(),
  skeleton_id uuid not null references skeletons(id) on delete cascade,
  notebook_id uuid not null references notebooks(id) on delete cascade,
  node_type text not null,
  title text not null,
  body text,
  source_positions jsonb,
  card_source text not null default 'ai_generated',
  rejected_at timestamptz,
  rejected_reason text,
  merged_into uuid references skeleton_nodes(id),
  created_at timestamptz not null default now()
);
create index if not exists idx_nodes_skeleton on skeleton_nodes(skeleton_id, node_type);
create index if not exists idx_nodes_notebook on skeleton_nodes(notebook_id);

-- 4. Many-to-many: node <-> direction
create table if not exists skeleton_node_directions (
  node_id uuid references skeleton_nodes(id) on delete cascade,
  direction_id uuid references learning_directions(id) on delete cascade,
  primary key (node_id, direction_id)
);

-- 5. Extend v1 tables
alter table documents add column if not exists summary text;
alter table cards add column if not exists skeleton_node_id uuid references skeleton_nodes(id) on delete set null;
alter table cards add column if not exists card_state text not null default 'unread';
alter table cards add column if not exists user_explanation text;
alter table messages add column if not exists skeleton_node_id uuid references skeleton_nodes(id) on delete cascade;

-- 6. Highlights
create table if not exists highlights (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references documents(id) on delete cascade,
  notebook_id uuid not null references notebooks(id) on delete cascade,
  chunk_id uuid references chunks(id) on delete set null,
  text text not null,
  created_at timestamptz not null default now()
);
create index if not exists idx_highlights_document on highlights(document_id);
