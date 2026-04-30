# Noto

> Notes, without the noise. 轻量记录 · 引导学习 · 专属知识库。

**Noto 不是 AI 总结器，也不是 AI 聊天版笔记。**
它是你阅读长资料时用的**主动消化工具** —— AI 先把文档拆成知识骨架，你再跟骨架互动、产生笔记、间隔复习，让学习真正发生。

当前版本：**v2.0**（[release notes](#v20-已实现) · [roadmap](#roadmap)）

---

## 核心理念

面对一篇长文 / 论文 / 代码仓库，AI 总结器会直接给你结论，让你"感觉读懂了"但其实跳过了真正的理解。Noto 的路径是：

1. **AI 先拆骨头**：上传资料 → 自动提炼 核心论点 / 概念 / 思考题 / 常见误解 + 跨文档学习方向
2. **你跟骨架互动**：每张骨架卡打开是一场苏格拉底对话（先问你，再提示，不替你思考）
3. **"懂了"有门槛**：用自己的话解释过 AI 才会把这张卡纳入复习队列
4. **原文随时可追溯**：每个结论都带页码锚点，一键跳回原文对照
5. **间隔复习沉淀**：SM-2 算法调度，自己评 again/hard/good/easy

所有 AI 预生成的内容都**明示是"可质疑的草稿"**，用户可以否决、合并、重写。

---

## 架构

```
React (Vite :5173)
    │
    │ HTTP / SSE
    ▼
FastAPI (:8000)
    │ ├─ LLM router (OpenAI-compatible + Anthropic + Google)
    │ ├─ 蒸馏 services (doc summary · space skeleton · explanation eval)
    │ ├─ RAG 检索 (pgvector 向量召回)
    │ └─ SM-2 复习调度
    ▼
Supabase
    ├─ Postgres + pgvector  (notebooks / documents / chunks / skeletons / nodes / cards / ...)
    └─ Storage  (原始 PDF/MD/TXT 文件)
```

**技术决策**：
- **前端**：React 18 + TypeScript + Vite · 无状态库 · 纯 CSS 设计 token（温润奶油色 · Noto Serif SC 衬线体 + Inter）
- **后端**：FastAPI + supabase-py · 49 pytest tests 覆盖纯函数与路由
- **数据**：Supabase（Postgres + pgvector + Storage）· 单 Postgres 连接，无 RLS（单用户）
- **LLM**：可插拔 provider（配置页填 base_url / api_key / model）· DeepSeek / Qwen / OpenAI / Claude / Gemini 皆可

完整设计见 [docs/superpowers/specs/2026-04-28-noto-v2-design.md](docs/superpowers/specs/2026-04-28-noto-v2-design.md)。

---

## 快速开始

### 1. Supabase 准备

- 在 [supabase.com](https://supabase.com) 创建新项目，拿到 Project URL 与 service_role key
- SQL Editor 里执行 [Noto/supabase/migrations/0001_init.sql](Noto/supabase/migrations/0001_init.sql)（v1 表 + pgvector + match_chunks 函数）
- 再执行 [Noto/supabase/migrations/0002_v2_schema.sql](Noto/supabase/migrations/0002_v2_schema.sql)（v2 骨架 + 卡片状态 + 高亮）

### 2. 后端

```bash
cd Noto/server
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

创建 `Noto/server/.env`（参考 `.env.example`）：

```
NOTO_AI_PROVIDER=openai
NOTO_AI_API_KEY=sk-...
NOTO_AI_BASE_URL=https://api.deepseek.com   # 或你自己的 provider
NOTO_AI_MODEL=deepseek-v4-pro

NOTO_EMBEDDING_PROVIDER=openai
NOTO_EMBEDDING_API_KEY=sk-...
NOTO_EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
NOTO_EMBEDDING_MODEL=text-embedding-v3       # 对齐 vector(1024)

NOTO_SUPABASE_URL=https://<ref>.supabase.co
NOTO_SUPABASE_SERVICE_KEY=<service_role_key>
```

启动：
```bash
uvicorn main:app --reload --port 8000
```

### 3. 前端

```bash
cd Noto/web
npm install
npm run dev
```

浏览器打开 http://localhost:5173。

---

## v2.0 已实现

### 🏠 空间首页（workspace）
- **空间概要**：AI 跨所有文档合成的 3-4 段学习导言（可"重新蒸馏"）
- **学习资料**：文档正方形卡（标题 / 摘要预览 / 进度 / 状态统计）· 拖放上传
- **学习方向**：AI 蒸馏的 3-6 条跨文档学习路径（编号 / 描述 / 预计时长）
- **常见误解**：2-3 条易错点预警
- **右栏 · 我的知识点**：用户笔记聚合（带状态色 + 来源文档）

### 📄 文档阅读页
- 顶部常驻**文档概要**（三段式：核心论点 / 主要脉络 / 关键结论）
- 中间**原文阅读区**（按 chunk 分段 · 带页码）
- 选中任意文字弹出**黑色浮动工具栏**：
  - **🎯 问 AI** — 右下角浮出 AI 回答小框（不造卡，用户可点"保存为笔记"再入库）
  - **⚠ 标记不懂** — 立即造 stuck 卡
  - **🖍 高亮** — 持久高亮（不造卡）
  - **📝 保存笔记** — 造 thinking 卡

### 🎯 学习方向页
- 按 方向 → 主张 / 概念 / 思考题 分组显示卡片
- 卡片 **4 状态机**：⚪ 未读 · 🤔 在想 · ✓ 懂了 · ⚠ 不懂

### 🧠 骨架卡互动
- 点开卡片 → **SocraticThread** 苏格拉底追问（流式回复）
- **✓ 懂了**：必须用自己的话解释 → AI 定性反馈（verdict + feedback + 漏点，**不打分**） → 进入 SM-2 复习队列
- **⚠ 不懂**：直接标记 · 集中在复习页的"不懂子队列"
- **× 否决 / ∞ 合并**：对 AI 骨架保留主动权

### 🔁 复习页（Focus mode）
- 占满屏，进度条 + 空间名 + 键盘提示
- 每张卡三态：Q 显现 → 揭示"上次的回答" → 4 档评分
- **键盘优先**：`Space` 显示 / `1-4` 评分 / `Esc` 退出
- 完成页显示本次统计 + 下次复习安排

### 📊 阶段报告
- 按日期范围生成 Markdown 三段：**已掌握 / 还模糊 / 下周建议**
- 数据源：空间内对话 + 复习统计 + 卡状态 + SM-2 评分历史

### 🔌 配置
- 可插拔 LLM：provider（openai 兼容 / anthropic / google）· base_url · api_key · model
- 单独的 embedding 配置（默认 fallback 到 LLM）
- Supabase URL + service_role key

---

## Roadmap

### v2.0.1（即将）
- **SocraticThread 持久化**：收起后不丢对话，重新打开能继续（需要 per-node conversation_id）
- **"问 AI" 的完整聊天**（当前只支持单轮问答）
- **笔记详情视图**：点"我的知识点"卡进详情页编辑
- **v1 遗留清理**：归档不再使用的 v1 conversations 表

### v2.1 · 代码阅读模式
- 上传单个 .py / .ts / .md 代码文件 · 语法高亮
- 选中函数 / 代码块 → AI 解释 + 文件:行 引用
- 代码骨架：入口 · 核心函数 · 数据流 · 调用链（简化版）

### v2.2 · 仓库智能
- 上传整个 repo（git archive / zip）
- AI 分析：入口识别 · 架构图 · 建议阅读路径
- 代码跨文件 RAG

### v2.3 · 阅读体验
- **PDF.js 完整渲染**（替代当前的 chunk-based 纯文本）
- **图片 / 公式块**（MathJax / KaTeX）
- **扫描 PDF 的 OCR**

### v3（战略）
- **跨文档概念合并**：多个空间 / 文档里的"反向传播"自动聚类成一张主概念卡
- **知识图谱视图**：笔记之间 backlink · 概念拓扑可视化
- **多人 / 协作 / 分享**：导出学习档案 · 家庭 / 小组版
- **移动端 / 暗色模式 / 快捷键系统**

---

## 目录结构

```
Noto/
├── Noto/
│   ├── server/            # FastAPI 后端
│   │   ├── routers/       # AI / notebooks / ingest / chat / cards / skeleton / review / report / highlights
│   │   ├── services/      # ai/ (provider router) · distill · evaluate · retrieval · document · sm2 · supabase_client
│   │   ├── prompts/       # socratic / distill_doc / distill_space / evaluate_explanation / card_extraction / report
│   │   ├── models/        # Pydantic schemas
│   │   └── tests/         # 49 pytest cases
│   ├── web/               # React + Vite 前端
│   │   ├── src/
│   │   │   ├── api/       # 统一 API client + SSE 解析
│   │   │   ├── layout/    # Shell · LeftSidebar · RightSidebar · Topbar
│   │   │   ├── components/# SkeletonCard · SocraticThread · GotItModal · SummaryCard · DocSquareCard · ...
│   │   │   └── pages/     # SpaceHomePage · DocReadingPage · DirectionPage · ReviewFocus · ConfigPage
│   │   └── public/noto-logo.png
│   └── supabase/
│       └── migrations/    # 0001 v1 base · 0002 v2 additions
├── docs/
│   ├── deep-research-report.md                  # 前期调研
│   └── superpowers/
│       ├── specs/
│       │   ├── 2026-04-27-noto-design.md        # v1 设计
│       │   └── 2026-04-28-noto-v2-design.md     # v2 设计 ★
│       └── plans/
│           ├── 2026-04-27-noto-v1.md            # v1 实施计划
│           └── 2026-04-28-noto-v2.md            # v2 实施计划 ★
├── image/                 # 品牌资源
├── CLAUDE.md              # Claude Code 入口引导
└── README.md
```

---

## 设计约束（硬性）

保证简洁、防止范围蔓延，v2 明确写进 spec 的 10 条硬约束：

1. 一个空间 = 一套 skeleton（非 per-doc）
2. 不做跨文档概念合并（v3）
3. 卡片总数硬顶 ≤ 30（AI prompt 层约束）
4. 评判用户"懂了"**不打分**，只定性反馈
5. 原文不做 PDF.js，文本 + 页码（v2.3）
6. 无"今日建议" / 无"跨文档自由提问"（已 v2 砍掉）
7. AI 评判用独立 prompt（不复用 Socratic）
8. 无暗色 / 无系统级快捷键（v3）
9. SSE 协议沿用 `data: {json}\n\n` + `[DONE]`
10. Socratic prompt 继承 v1 · 加约束"对话发生在某张卡的上下文里"

---

## License

MIT（自用项目，欢迎 fork / 学习）
