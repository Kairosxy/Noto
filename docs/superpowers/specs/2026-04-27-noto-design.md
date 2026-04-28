# Noto v1 设计稿

**日期**：2026-04-27
**状态**：已确认（由 brainstorming 产出）
**作者**：lixiangyu + Claude

---

## 1. 产品定位

Noto 是「**资料驱动的 AI 学习教练**」：用户上传学习资料 → AI 用苏格拉底式提问引导学习 → 自动提炼复习卡 → 按周生成掌握度报告。

**不是**什么：不是聊天机器人、不是笔记应用、不是 NotebookLM。核心差异点是**引导式学习闭环**（先问你，再提示，最后讲解；然后进入间隔复习 + 掌握度评估）。

**v1 只服务一个用户（作者本人）**，不做认证 / 订阅 / 多租户 / 合规。

---

## 2. 核心体验流

```
首次启动
  └─ 配置 LLM（provider / base_url / api_key / chat_model / embedding_model）

创建「学习空间」（Notebook）
  └─ 起名 + 描述学习目标

上传资料（PDF / MD / TXT / DOCX）
  └─ 后端解析 → 分块 → 嵌入 → 写入 Supabase

进入「学习对话」（核心）
  ├─ AI 苏格拉底式开场：先问用户一个问题
  ├─ 用户回答 → AI 先给提示，不直接讲
  ├─ 再答 → AI 半讲解 → 要求用户用自己的话复述（费曼）
  ├─ 右侧显示本轮引用的资料片段（页码可跳原文）
  └─ 手动点「结束本轮」→ AI 提炼 3-5 张复习卡入库

「今日复习」入口
  └─ 到期卡一张张过；评分（again/hard/good/easy）→ 简版 SM-2 重算到期日

「阶段报告」按钮（手动触发）
  └─ 指定日期范围（默认最近 7 天）的对话 + 复习记录 → LLM 出 markdown 报告：
     已掌握 / 还模糊 / 下周建议
```

---

## 3. 架构

### 3.1 三层分层

```
┌────────────────────────────┐
│   浏览器 (Vite + React)    │  只负责 UI + 调 Python API
└───────────┬────────────────┘
            │ HTTP / SSE
            ▼
┌────────────────────────────────────────────────────┐
│   Python FastAPI (localhost:8000)                  │
│   - LLM router（复用 learn-flow 模式）             │
│   - 文档解析 / 分块 / 嵌入                         │
│   - RAG 检索                                       │
│   - 复习调度 / 报告生成                            │
└──────┬───────────────────────┬─────────────────────┘
       │                       │
       ▼                       ▼
┌─────────────────┐   ┌─────────────────────┐
│  Supabase       │   │  LLM Provider       │
│  Postgres       │   │  (用户配置的)       │
│  + pgvector     │   │  - /chat            │
│  + Storage      │   │  - /embeddings      │
└─────────────────┘   └─────────────────────┘
```

### 3.2 分层原则

- **前端只调 FastAPI**，不直接碰 Supabase（边界清楚，不用 RLS）
- **FastAPI 用 service role key 连 Supabase**（单用户本地跑，安全无问题）
- **LLM router 参考 learn-flow 的 `services/ai/` 结构**（base + manager + 三个 provider + utils），但只在 Noto 仓库内新写，不共享代码
- **Embedding 不做第二套抽象**：一个函数搞定，内部 if-provider

---

## 4. 数据模型

### 4.1 表结构（Supabase Postgres）

```sql
-- 学习空间
notebooks (
  id uuid primary key,
  title text not null,
  goal text,                -- 学习目标自由描述
  created_at timestamptz default now()
)

-- 原始上传文件
documents (
  id uuid primary key,
  notebook_id uuid references notebooks(id) on delete cascade,
  filename text not null,
  storage_path text not null,       -- Supabase Storage 路径
  mime text,
  pages int,
  status text,                       -- 'parsing' | 'ready' | 'failed'
  created_at timestamptz default now()
)

-- 文档切块 + 向量
chunks (
  id uuid primary key,
  document_id uuid references documents(id) on delete cascade,
  content text not null,
  page_num int,                      -- 原 PDF 页码，可空
  position int not null,             -- 在文档内的顺序
  embedding vector(1024),            -- pgvector，维度跟随用户 embedding 模型
  created_at timestamptz default now()
)
create index on chunks using ivfflat (embedding vector_cosine_ops);

-- 学习对话会话
conversations (
  id uuid primary key,
  notebook_id uuid references notebooks(id) on delete cascade,
  title text,                         -- 空则 UI 显示首条用户消息前 30 字
  status text not null,               -- 'active' | 'closed'
  started_at timestamptz default now(),
  closed_at timestamptz
)

-- 对话消息
messages (
  id uuid primary key,
  conversation_id uuid references conversations(id) on delete cascade,
  role text not null,                 -- 'user' | 'assistant'
  content text not null,
  citations jsonb,                    -- [{chunk_id, page_num}, ...]，user 消息为 null
  created_at timestamptz default now()
)

-- 复习卡（对话结束时 LLM 提炼）
cards (
  id uuid primary key,
  notebook_id uuid references notebooks(id) on delete cascade,
  source_conversation_id uuid references conversations(id) on delete set null,
  question text not null,
  answer text not null,
  due_at timestamptz not null default now(),
  ease int not null default 0,        -- 连续答对次数
  reps int not null default 0
)

-- 每次复习的记录
reviews (
  id uuid primary key,
  card_id uuid references cards(id) on delete cascade,
  rating text not null,               -- 'again' | 'hard' | 'good' | 'easy'
  reviewed_at timestamptz default now()
)

-- 阶段评估报告
reports (
  id uuid primary key,
  notebook_id uuid references notebooks(id) on delete cascade,
  from_date date,
  to_date date,
  content text not null,              -- markdown
  generated_at timestamptz default now()
)
```

### 4.2 Storage

一个 bucket `documents/`，按 `{notebook_id}/{document_id}.{ext}` 组织。不做图片缩略图等附加处理。

---

## 5. Python FastAPI 后端

### 5.1 目录结构

```
Noto/server/
├── main.py                   # app 装配 + CORS + lifespan（挂载 config/ai_manager/supabase_client）
├── config.py                 # 三层配置：默认 → .env → data/config.json
├── routers/
│   ├── ai.py                 # /api/ai/chat（SSE） /test-connection
│   ├── notebooks.py          # CRUD
│   ├── ingest.py             # POST /upload  POST /parse-and-embed
│   ├── chat.py               # POST /send（RAG + LLM SSE） 列消息
│   ├── review.py             # GET /due  POST /rate  POST /close-conversation
│   └── report.py             # POST /generate  GET /:id
├── services/
│   ├── ai/
│   │   ├── base.py           # AIProvider 抽象
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── google_provider.py
│   │   ├── manager.py        # 工厂 + 动态导入
│   │   ├── utils.py          # sse_event / SSE_DONE / extract_json
│   │   └── embedding.py      # 单函数：embed(texts, provider, base_url, key, model)
│   ├── supabase_client.py    # supabase-py 单例（service role）
│   ├── document.py           # parse(file) → (text, pages)；chunk(text, pages) → [chunks]
│   ├── retrieval.py          # search(notebook_id, query, k=5) → [chunk]
│   └── sm2.py                # next_due(rating, ease, reps) → (due_at, ease, reps)
├── models/schemas.py         # 所有 Pydantic 请求/响应
├── prompts/
│   ├── socratic.md
│   ├── card_extraction.md
│   └── report.md
├── requirements.txt
└── .env.example
```

### 5.2 关键接口

| 方法   | 路径                               | 说明                                                                 |
| ------ | ---------------------------------- | -------------------------------------------------------------------- |
| POST   | `/api/ai/test-connection`          | 用临时参数 ping 一次 LLM                                             |
| POST   | `/api/notebooks`                   | 创建学习空间                                                         |
| GET    | `/api/notebooks`                   | 列学习空间                                                           |
| POST   | `/api/ingest/upload`               | 上传文件 → Supabase Storage，返回 document_id，状态 `parsing`        |
| POST   | `/api/ingest/parse-and-embed`      | 后台任务：解析 + 分块 + 嵌入 + 入库，完成后状态 `ready`              |
| POST   | `/api/chat/send`                   | SSE：检索 → 拼 prompt → 流式返回；结束时 upsert 用户+助手消息         |
| POST   | `/api/chat/close-conversation`     | 触发 LLM 提炼复习卡 + 关闭对话                                       |
| GET    | `/api/review/due?notebook_id=`     | 返回到期卡（按 due_at 升序）                                         |
| POST   | `/api/review/rate`                 | `{card_id, rating}` → 更新 ease/reps/due_at + 插入 reviews 记录      |
| POST   | `/api/report/generate`             | `{notebook_id, from_date, to_date}` → LLM 生成 markdown 报告并存库    |

### 5.3 配置（`config.py`）

三层优先级：硬编码默认值 → `.env` → `data/config.json`（UI 可改）。

字段：

```python
# LLM
ai_provider: str         # openai | anthropic | google
ai_api_key: str
ai_base_url: str
ai_model: str

# Embedding（允许与 chat 同源或不同源；任一字段为空则 fallback 到对应 ai_* 字段）
embedding_provider: str
embedding_api_key: str
embedding_base_url: str
embedding_model: str          # 此字段必须非空，否则视为未配置

# Supabase
supabase_url: str
supabase_service_key: str
```

---

## 6. 前端（Vite + React）

### 6.1 目录结构

```
Noto/web/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── pages/
│   │   ├── ConfigPage.tsx         # LLM + Supabase 配置
│   │   ├── NotebooksPage.tsx      # 学习空间列表
│   │   ├── NotebookDetail.tsx     # Tab: Docs | Chat | Review | Report
│   │   └── ReviewSession.tsx      # 复习过卡界面
│   ├── components/
│   │   ├── ChatView.tsx           # 流式渲染 + 引用侧栏 + 「结束本轮」按钮
│   │   ├── CitationPanel.tsx
│   │   ├── UploadZone.tsx
│   │   ├── Flashcard.tsx          # 正面/反面 + 四档评分按钮
│   │   └── ReportView.tsx
│   ├── api/client.ts              # fetch 薄包装 + SSE 解析
│   └── store/config.ts            # useState + useContext，存 LLM 配置缓存
├── index.html
├── package.json
└── vite.config.ts
```

### 6.2 状态管理

- **不引入 zustand / redux / react-query**
- 页面数据就地 `useState` + `useEffect`
- 全局只有一个 `ConfigContext`（LLM 配置是否就绪）

### 6.3 SSE 解析

`api/client.ts` 里一个 `streamChat(req, onChunk)` 函数，内部用 `fetch` + `ReadableStream` 手工切 `data: ...\n\n` 解析 JSON 块（`[DONE]` 结束）。不用 `EventSource`（因为 `POST` 不支持）。

---

## 7. 苏格拉底式 Prompt 骨架

`prompts/socratic.md`（system）：

```
你是 Noto，一位坚持「先让学习者思考」的导师。

[资料引用]
{top-5 chunks, 带 page_num}

[学习空间目标]
{notebook.goal}

[本轮已说]
{最近 10 条消息}

[铁律]
1. 除非学习者明确说「直接讲」，否则绝不一次性给完整答案。
2. 标准流程：提问 → 听回答 → 指出模糊点 → 给一条提示 → 再听 → 讲半步 → 要求用自己的话复述（费曼）。
3. 每次用到资料，标注引用 [p.{page_num}]。
4. 学习者明显卡住（≥2 次「不知道」）才进入完整讲解。
5. 回答尽量短，强迫学习者多说。
```

`prompts/card_extraction.md`（user 消息拼整轮对话 transcript）：
- 系统指令：从下述对话中提炼 3-5 张闭卷复习卡；每张必须能单独作答（问题自包含上下文，不引用"刚才那个")；严格返回 JSON 数组 `[{"question": str, "answer": str}]`，不带 markdown 代码块以外的任何解释。
- 后端用 `extract_json` 解析；解析失败则返回 4xx 要求重试，不入库。

`prompts/report.md`（user 消息拼 transcript 摘要 + 复习统计 JSON）：
- 输入：`{from_date, to_date, conversations: [{title, summary}], review_stats: {total, again, hard, good, easy}, top_cards: [{question, answer, ease, reps}]}`
- 输出：一段 markdown，恰好三级标题 `## 已掌握` / `## 还模糊` / `## 下周建议`；每段下面是要点列表，不加任何前言/后记。

---

## 8. RAG 检索策略

**第一版只做向量检索，不做 FTS / RRF / rerank。**

```sql
select id, document_id, content, page_num
from chunks
where document_id in (
  select id from documents where notebook_id = $1 and status = 'ready'
)
order by embedding <=> $2
limit 5;
```

召回不够再加 FTS 或 rerank，不提前优化。

---

## 9. 复习调度（简版 SM-2）

`services/sm2.py`：

```python
def next_due(rating: str, ease: int, reps: int) -> tuple[datetime, int, int]:
    if rating == "again":
        return (now + 1day, 0, reps + 1)
    if rating == "hard":
        return (now + 3day, max(0, ease), reps + 1)
    if rating == "good":
        return (now + 7day * (ease + 1), ease + 1, reps + 1)
    if rating == "easy":
        return (now + 21day * (ease + 1), ease + 2, reps + 1)
```

无遗忘因子、无逾期惩罚。够用且直观。

---

## 10. 简洁约束（硬性）

这 10 条写进 spec 是为了约束实现，防止后续过度设计：

1. **LLM router 直接 port learn-flow 的最小集**，不扩展（不加 retry / token 计数 / cost tracking）。
2. **`embedding.py` 不做第二套抽象**：一个函数 `async def embed(texts, ...)`，内部 `if provider ==`。
3. **Supabase 只当数据库用**：不用 RLS、不用 auth、不用 Edge Function、不用 realtime。
4. **RAG 第一版只用向量**：pgvector `<=>` + `LIMIT 5`，一条 SQL。
5. **Chunking 一个函数**：按段落切，目标 ~800 tokens，超长段落硬切；不做 heading path / overlap。
6. **前端不搞状态库**：`useState` + 一个 `ConfigContext`。
7. **Prompt 集中三份**：`socratic.md` / `card_extraction.md` / `report.md`，无 prompt chain 引擎。
8. **表只建 7 张**，字段只留用到的（不加 `updated_at` / soft delete / version）。
9. **对话历史不做截断/摘要**：直接塞最近 N 条，超了再说。
10. **SSE 格式抄 learn-flow 的 `sse_event` + `[DONE]`**：不加心跳、不加断线重连。

---

## 11. v1 明确砍掉（YAGNI）

- 用户认证 / 多租户 / 权限
- 订阅 / 付费墙 / 使用量限制
- 番茄钟组件（prompt 里提一句就够）
- 康奈尔笔记自动左右栏（复习卡已替代）
- SQ3R / 西蒙学习法 的显式页面（融进 prompt）
- 敏感信息识别 / 个性化关闭 / 跨境合规 / 未成年人保护
- 多模态输入（图片 / 语音）
- OCR（扫描 PDF 跳过）
- 题库 / 错题本（与复习卡合并）
- 夜间模式 / 国际化 / 分享 / 导出
- 移动端原生 app

---

## 12. 目录快照

```
Noto/
├── Noto/
│   ├── server/           # FastAPI 后端
│   ├── web/              # Vite + React 前端
│   └── supabase/
│       ├── migrations/0001_init.sql     # 表 + pgvector + 索引
│       └── README.md
├── image/
│   └── logo.png
└── docs/
    ├── deep-research-report.md
    └── superpowers/
        ├── specs/2026-04-27-noto-design.md
        └── plans/2026-04-27-noto-v1.md
```

---

## 13. 里程碑切分（仅供 writing-plans 参考）

v1 切成三个可验收步骤，每步都能独立跑起来：

1. **M1 — LLM 通路 + 配置页**：能配 LLM、测连接、跑一次不带 RAG 的普通流式聊天
2. **M2 — 上传 + RAG 对话**：能上传 PDF、构建 chunk + embedding、苏格拉底式对话带引用
3. **M3 — 复习卡 + 报告**：关闭对话自动提卡、到期卡复习、生成阶段报告

具体任务拆分由 writing-plans 阶段产出 `docs/superpowers/plans/` 下的实现计划。
