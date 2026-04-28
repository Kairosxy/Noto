# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What Noto is

AI learning coach: user uploads study materials → AI guides learning via Socratic questioning with citations → auto-extracts flashcards at end of conversation → SM-2 spaced repetition + weekly assessment reports.

Personal MVP (single-user), tagged `v0.1.0`. Design rationale in [docs/superpowers/specs/2026-04-27-noto-design.md](docs/superpowers/specs/2026-04-27-noto-design.md); implementation history in [docs/superpowers/plans/2026-04-27-noto-v1.md](docs/superpowers/plans/2026-04-27-noto-v1.md).

## Repo layout quirk

The repo root contains `Noto/Noto/` (nested). The outer `/home/lixiangyu/lxy/app/Noto/` is the repo root; the inner `Noto/` holds all app code (`server/`, `web/`, `supabase/`). Don't "fix" this — code paths assume it.

## Commands

All commands assume repo root as cwd unless noted.

**Backend** (`Noto/server/`):
```bash
cd Noto/server
source .venv/bin/activate              # venv created by plan Task 1
pytest -q                              # all tests (39 expected)
pytest tests/test_foo.py::test_bar -v  # single test
uvicorn main:app --reload --port 8000  # dev server
```

**Frontend** (`Noto/web/`):
```bash
cd Noto/web
npm run dev                            # vite dev server on :5173, /api proxied to :8000
npx tsc -b --noEmit                    # typecheck only
npm run build                          # full production build
```

**Full local run:** both servers in separate terminals, then http://localhost:5173.

## Architecture

Three layers with hard boundaries:

```
React (Vite :5173)  →  FastAPI (:8000)  →  Supabase (Postgres+pgvector+Storage)
                                        →  LLM Provider (user-configured)
```

**Frontend never talks to Supabase directly.** All data flows through the FastAPI server, which uses a Supabase service-role key. This avoids RLS complexity for a personal app.

### LLM router (the single most important abstraction)

Lives in `Noto/server/services/ai/`. Pattern:

- `base.py` — `AIProvider` ABC: `chat` / `chat_stream` / `test_connection`
- `openai_provider.py` / `anthropic_provider.py` / `google_provider.py` — concrete impls
- `manager.py` — `AIProviderManager` picks provider via **dynamic import** (don't preload all SDKs); also exposes classmethod `test_with_params` for the UI's "test connection" flow
- `utils.py` — SSE helpers (`sse_event`, `SSE_DONE`, `SSE_HEADERS`, `extract_json`)
- `embedding.py` — **intentionally a single function**, not a class hierarchy (per spec simplicity constraint #2). Only supports OpenAI-compatible endpoints for embeddings because Anthropic has no embedding API and Qwen/DeepSeek/Ollama are all OpenAI-compatible

All providers use a lazy `_get_client()` so tests can monkeypatch it without any real network.

### Config & state wiring

`config.py` loads in three tiers: hardcoded defaults → `.env` → `data/config.json` (the UI writes this when the user saves settings). `effective_embedding()` falls back empty fields to their `ai_*` equivalents; only `embedding_model` is required explicitly.

`app.state` is populated **inside `create_app()`**, NOT in `lifespan`. TestClient doesn't run lifespan unless used as a context manager, so putting state in `create_app()` keeps unit tests simple. The empty `lifespan` is still there for future async startup if needed.

When `/api/settings` saves new config, the route reloads config, swaps `app.state.config`, and calls `.refresh(new_cfg)` on both `ai_manager` and `supabase`. Both managers are lazy — they rebuild the actual client on next use.

### Data flow: learning loop

1. **Upload** (`POST /api/ingest/upload`) → file → Supabase Storage → insert `documents` row with `status=parsing` → return immediately. A FastAPI `BackgroundTask` runs `_process_document`: parse → chunk → embed → insert `chunks` rows → flip status to `ready` (or `failed`). The UI polls the documents list every 3s when any is still `parsing`.

2. **Chat** (`POST /api/chat/send`, SSE) → embed user message → pgvector similarity search via `match_chunks` RPC → fill Socratic `prompts/socratic.md` template (`{citations}`, `{goal}`) → stream LLM response. The **first SSE frame carries `conversation_id + citations` metadata** before any content chunks — the UI uses this to show the citation panel before the answer arrives.

3. **Close conversation** (`POST /api/chat/close-conversation`) → send whole transcript to LLM with `prompts/card_extraction.md` → parse JSON array via `extract_json()` (handles ```json fences and bare JSON) → insert `cards` with `due_at=now()`.

4. **Review** (`GET /api/review/due`, `POST /api/review/rate`) → `services/sm2.py` has the scheduler. 4 buckets: `again`→1d (reset ease), `hard`→3d (same ease), `good`→7·(ease+1)d (ease+1), `easy`→21·(ease+1)d (ease+2). No forgetting factor.

5. **Report** (`POST /api/report/generate`) → aggregate conversations + cards + review stats for date range → LLM with `prompts/report.md` → markdown with exactly `## 已掌握` / `## 还模糊` / `## 下周建议`.

### SSE framing

Custom, not `EventSource` (POST not supported). Format: `data: {json}\n\n`, terminated by `data: [DONE]\n\n`, errors as `data: {"error": "..."}\n\n`. Frontend parser is in `Noto/web/src/api/client.ts::streamSSE`.

## Simplicity constraints (from design spec §10)

These are **hard rules** to prevent scope creep. Don't add retry logic, token counting, cost tracking, FTS/RRF/rerank, chunking heading-awareness, chunk overlap, state libraries (zustand/redux), API-key proxy layers, or RLS unless explicitly asked.

Current v1 has 7 tables (not 8 — `reviews` is log-only, counted separately), ~800-token chunks split by paragraph, pure vector retrieval with `LIMIT 5`, zero UI polish beyond basic CSS.

## Gotchas already paid for

- **pgvector dimension must match your embedding model.** Migration uses `vector(1024)` (Qwen `text-embedding-v3`). OpenAI `text-embedding-3-small` is 1536 — change both `chunks.embedding` and `match_chunks(p_query vector(N))` BEFORE inserting data (dimensions are immutable once populated).
- **The `match_chunks` SQL function is appended at the bottom of `0001_init.sql` but wasn't in the initial run.** If chat returns `PGRST202 Could not find the function`, re-run that block in the Supabase SQL Editor.
- **Qwen embedding batch limit is 10.** `services/ai/embedding.py` batches at 10 for universal safety. Don't remove this.
- **Postgres `text` rejects `\x00`.** Some PDFs (malformed fonts, OCR artifacts) leak NUL bytes through pypdf. `services/document.py::_sanitize` strips them at the source. Keep this.
- **`.env` vs `.env.example`.** `.env` is in `.gitignore` — real secrets go there. `.env.example` is committed as a template with empty placeholders. Never put real keys in `.example` files.
- **`_project_root()` in `config.py` is `Path(__file__).parent.parent`** (inner Noto, parent of `server/`), not `.parent`. The `data/` dir lives at `Noto/server/data/`, and this is what `.gitignore` expects.

## Supabase setup (for new environment)

1. Create project at supabase.com, grab URL + **service_role** key
2. Paste entire `Noto/supabase/migrations/0001_init.sql` into SQL Editor, run it (creates 7 tables + `match_chunks` function + `documents` storage bucket, all idempotent)
3. Put URL + service key into `Noto/server/.env` (`NOTO_SUPABASE_URL`, `NOTO_SUPABASE_SERVICE_KEY`) or configure via the `/config` UI

## TDD convention

Backend pure functions and routes are test-first (config / providers / manager / embedding / document / sm2 / retrieval). Frontend UI is manual-verification only. When adding a backend feature, write the failing test first and keep the existing 39 green.
