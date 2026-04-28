# Noto v2 设计稿

**日期**：2026-04-28
**继承**：[v1 设计稿](2026-04-27-noto-design.md)
**状态**：已确认（brainstorming 产出）
**参考原型**：`.superpowers/brainstorm/*/content/v2-prototype.html`（git-ignored 但可在本地浏览器查看）

---

## 1. 使命与产品理念

**使命不变（继承 v1）**：
> 帮用户在 AI 辅助下，把长/密/难的资料变成真正属于自己的理解；一切结论可追溯；优先引导、不直接给答案；有间隔复习、有阶段评估。

**变的是主交互原语**：
- v1 原语 = **对话**（Socratic 对话绑 RAG 引用）
- v2 原语 = **知识骨架卡 + 笔记**（AI 蒸馏 + 用户笔记一起构成空间的知识图）

**一句话产品定位**：
> v2 Noto 不是 ChatGPT 的笔记版，也不是 Anki 的 AI 版。它是**你阅读长资料时用的主动消化工具** —— AI 先拆骨头，你再跟骨架互动，笔记自然沉淀，跨文档连成你对一个主题的理解。

**与 ChatGPT 的本质区别（防止回退到 chat-as-canvas）**：
- 打开 app 看到的不是空聊天框，而是"这个主题你积累了多少"的知识地图
- AI 的每句话都绑原文锚点（可点回原文对照）
- "懂了"有门槛（必须用自己的话 + AI 评判掌握度），不是一个按钮
- 笔记是第一公民（用户的理解沉淀），不是聊天历史

---

## 2. 核心模型

### 2.1 两层结构

```
空间（Space · 主居所 · 用户大部分时间在这里）
  ├─ 空间级学习方向       ← AI 跨文档蒸馏
  ├─ 空间级常见误解       ← AI
  ├─ 我的知识点          ← 用户笔记聚合（跨所有文档）
  └─ 学习资料            ← 多份文档（点进去才见具体）

文档（Document · 辅 · 需要深挖时进入）
  ├─ 内容总结            ← AI 生成，顶部常驻
  ├─ 原文阅读视图        ← 选中文本 → AI 解释 / 标不懂 / 保存笔记
  └─ 本文档笔记          ← 同一份笔记同时出现在空间级"我的知识点"里
```

### 2.2 笔记是双层之间的血管

笔记一旦产生，就同时存在于：
- **文档内部**（绑定原文位置，属于这份文档的阅读痕迹）
- **空间首页**（按主题聚合进"我的知识点"，跨文档共有的积累）

**笔记"先轻后重"三级**（避免新用户被结构吓退）：

| 级别 | 必填字段 | 可出现状态 |
|---|---|---|
| **轻量笔记**（保存即可）| `question` · `ai_explanation` · `source_positions` · `state=thinking` | 在空间首页"我的知识点"列表显示 |
| **标记懂了**（触发复习）| 加 `user_explanation`（自己的话） | 状态变 `got_it` · 进入 SM-2 队列 |
| **标记不懂**（AI 补课）| 无新增 | 状态变 `stuck` · 不进复习 · 单独列表 |

笔记的完整字段：
- `title`：笔记标题（AI 初稿，用户可改）
- `question`：触发这条笔记的问题
- `ai_explanation`：AI 的解释
- `user_explanation`：用户"自己的话"（**仅 got_it 状态需要**）
- `source_positions`：原文锚点（document_id + chunk_id + page_num）
- `state`：4 状态机（unread / thinking / got_it / stuck）
- `due_at / ease / reps`：SM-2 字段（got_it 状态才激活）

**关键语义**：保存笔记 ≠ 必须写自己的话。用户可以"看完 AI 解释，觉得有价值就保存了，但暂时说不清"。过几天回来再补充，标"懂了"。

---

## 3. 上传即蒸馏（空间级）

### 3.1 生成流程

```
用户上传新文档到空间
  ↓
后端：解析 + 分块 + 嵌入（v1 管线复用）
  ↓
LLM 调用 1：为这份文档生成「内容总结」（核心论点 / 主要脉络 / 关键结论，300-500 字）
  ↓
LLM 调用 2：重新蒸馏「空间级方向 + 误解 + 概念」
  输入 = 空间内所有文档的 summary + 代表性 chunks
  输出 = learning_directions / pitfalls / concepts（含每张卡的原文锚点）
  ↓
写入 skeletons · skeleton_nodes · learning_directions
  ↓
空间首页自动刷新
```

### 3.2 产物结构

**每份文档有**：
- 1 份 `summary`（AI 生成，三段式：核心论点 / 主要脉络 / 关键结论）

**每个空间有**（动态，新增文档时重算）：
- 1 份 **`space_summary`**（AI 跨文档合成 · 3-4 段 markdown：这个空间研究什么 · 收录了哪些资料 · 它们共同回答了什么问题）
- N 个 `learning_directions`（≤ 6 条，每条带 name / description / estimated_minutes / 关联卡片）
- M 张 `pitfalls`（≤ 3）
- 概念术语表（≤ 15 个）

### 3.3 硬约束（防止卡片爆炸）

- 学习方向总数 ≤ 6
- 每个方向下卡片 ≤ 8
- 误解 ≤ 3
- 空间级总卡数硬顶 **≤ 30**（强迫 LLM 做重要性筛选）

---

## 4. 知识骨架卡 · 状态机与交互

### 4.1 4 种状态

| 状态 | 图标 | 进入条件 |
|---|---|---|
| ⚪ unread | 空圈 | 默认 |
| 🤔 thinking | 橙圈 | 用户展开卡 / 开始对话 |
| ✓ got_it | 绿勾 | 用户写了自己的话 + AI 评判 mastery ≥ 60（或用户强制通过）|
| ⚠ stuck | 红感叹 | 用户主动标记 / 连续 ≥2 次"不知道" |

### 4.2 卡片点开后的 Socratic 追问流

```
用户点卡（claim / concept / question）
  ↓
卡原地展开（不弹窗、不跳转）
  ↓
AI 开场问：一个不直接给答案的苏格拉底问题（继承 v1 socratic.md 铁律）
  ↓
用户输入回答
  ↓
AI 给提示（不判对错，点出模糊点）
  ↓
用户再答 → AI 半讲解 + 原文引用（可点 [p.42] 跳抽屉）
  ↓
用户选：
  · 标"✓ 懂了"（弹出输入框填自己的话 → AI 质性 feedback → 进 SM-2）
  · 标"⚠ 不懂"（AI 补前置知识卡 / 换角度）
  · 继续追问
  · 收起（状态保持在"🤔 在想"）
  · **× 否决此卡**（骨架卡不适用或重复 → 软删除，从骨架视图消失，记录供未来 prompt 调优）
  · **∞ 合并到其他卡**（发现与另一张卡讲的是同一件事 → 合并）
```

**否决 / 合并**是为了让用户对 AI 蒸馏出的骨架有主动权 —— 不是"读完被迫接受 25 张卡"，而是"阅读过程中塑形"。

### 4.3 "懂了"评判（AI 质性反馈，非打分）

**设计原则**：AI 不给用户打分。AI 做的是**帮用户看漏点**，判分的责任在用户自己（复习时用 SM-2 四档评自己）。

用户写完自己的话，LLM 返回结构化 JSON：
```json
{
  "verdict": "pass" | "can_deepen",
  "feedback": "一段温和的反馈（≤ 100 字）",
  "missing_points": ["关键漏点 1", "关键漏点 2"]
}
```

**规则**：
- **所有用户的解释都通过**（verdict 只影响 feedback 口吻，不阻塞）
  - `pass` → "你抓住了关键，这里可以更深入..."
  - `can_deepen` → "建议再想想这几点..."
- 卡片状态变为 `got_it` · **初始 due = now + 1 day**（不再按掌握度分级）
- 后续复习让用户自评（again/hard/good/easy），SM-2 真实响应用户主观难度
- UI 显示：`✓ 懂了 · 下次复习明天 · [AI 点出 3 个可以更深的点]`

**为什么不打分**：
- LLM 对"用自己的话解释某概念"的自动评分现在做不准，会误判
- 自动高分 → 虚假自信；自动低分 → 挫败放弃
- SM-2 本身就是靠用户主观评分收敛，没必要两层评估

---

## 5. 空间首页布局

### 5.1 三栏结构

```
┌─ 左栏 ──────┬─ 主区（焦点） ────────┬─ 右栏 ─────────┐
│ Noto logo   │                        │ 📝 我的知识点   │
│             │                        │   · 链式法则 88%│
│ 学习空间     │  📚 学习资料          │   · 反向传播 82%│
│  ● 深度学习  │     (正方形卡片网格)   │   · ReLU 🤔     │
│    GPT-4    │                        │   · 饱和 ⚠      │
│    线性代数  │  🎯 学习方向          │   · ...         │
│    + 新建   │     (3-6 张方向卡)     │                  │
│             │                        │                  │
│             │  ⚠ 常见误解           │                  │
│             │     (≤3 张)            │                  │
│             │                        │                  │
│ ⚙ 设置 🔁复习│                       │                  │
└─────────────┴────────────────────────┴──────────────────┘
```

### 5.2 左栏（空间导航）

- Noto logo（用真实品牌 SVG/PNG，不是 CSS fallback）
- 空间列表（扁平，不嵌套文档）
- 底部：设置 · 🔁 复习 N（点击进入 review focus mode）

### 5.3 主区（学习焦点）

**顺序严格固定**：
1. 📄 **空间概要** — AI 跨文档合成的空间级概要（3-4 段 markdown · 带"重新蒸馏"按钮）。**标题下方常驻一行 disclaimer**："这是 AI 整理的阅读草稿 · 发现不对可以质疑 / 修改 / 删除"。新空间还没资料时显示空状态提示"上传第一份资料开始学习"。
2. 📚 **学习资料** — 每份文档一张正方形卡（~210x200px），显示：标题 / 简短摘要（3 行夹断）/ 进度条 / 懂·在想·不懂统计。点击进入该文档的阅读视图。
3. 🎯 **学习方向** — 横向长条卡，每条显示：编号 / 标题 / 描述 / 卡数 · 预计时长 · 源文档 / 进度条。点击进入该方向的卡片集合。
4. ⚠ **常见误解** — 2 列小卡，每条一句。

**不在主区**：今日建议 · 跨文档自由提问（都移除，避免信息噪音）。

### 5.4 右栏（我的知识点）

- 标题 + 笔记总数 + "按主题 ▾" 切换
- 每张笔记卡：标题（衬线体）+ 掌握度徽章 / 状态 + 原文锚点（灰色）
- 点击卡 → 打开笔记详情视图（v2.0 先做简化版：修改弹窗 / 跳原文）

### 5.5 顶部 stats bar

- 空间名 · 目标 · 🔥 连续天数
- 聚合统计：懂 N / 在想 M / 不懂 K
- 动作：🔁 复习 / 📊 报告 / ⚙

---

## 6. 文档阅读视图

进入路径：空间首页点某张文档正方形卡 → 阅读视图。

### 6.1 布局

```
┌ 顶部面包屑：← 返回空间首页                  ┐
│                                            │
│  📄 概要 · 第 3 章：反向传播  [重新蒸馏]    │ ← 顶部常驻总结
│  ## 核心论点                                │
│  ## 主要脉络                                │
│  ## 关键结论                                │
│                                            │
│ ┌─────────────────────────────────────┐   │
│ │ 📑 目录   第 3.2 节 · p.42/45  ↑ ↓ │   │
│ ├─────────────────────────────────────┤   │
│ │ 3.2 反向传播                         │   │ ← 原文阅读区
│ │                                      │   │   选中文本出浮动工具栏：
│ │ 前馈神经网络通过前向传播...            │   │    🎯 问 AI / ⚠ 标不懂
│ │ [选中的句子：反向传播算法...]          │   │   / 🖍 高亮 / 📝 保存为笔记
│ │                                      │   │
│ │ ... 更多段落 ...                      │   │
│ └─────────────────────────────────────┘   │
└────────────────────────────────────────────┘
（右栏"我的知识点"保持常驻，提示本文档产生的笔记会出现在这）
```

### 6.2 选中文本的交互

1. 用户选中原文任意一段
2. 浮动工具栏出现（黑色小条）：
   - **🎯 问 AI** → 弹出输入框，问题自动把选中文本附上下文 → AI 回答（带原文引用）→ 对话进行时自动创建一张 `user_selection` 类型的 skeleton_node + card；用户满意后可"标记懂了"转入复习
   - **⚠ 标记不懂** → 直接创建一张 `user_selection` 卡，状态 `stuck`，附带选中文本，AI 自动生成解释 + 可能的前置知识
   - **🖍 高亮** → 持久高亮（存 highlights 表），不创建 node/card
   - **📝 保存为笔记** → 创建 `user_selection` node + card，状态 `thinking`，等用户补充

> 统一语义：**问 AI / 标不懂 / 保存笔记** 三者都会生成一张 skeleton_node（类型 `user_selection`），只是初始状态不同。用户的任何"深度交互"都落到同一个卡片模型，空间首页的"我的知识点"能看到它们。

### 6.3 原文呈现

v2.0 MVP：
- **PDF**：提取文本 + 页码，以 markdown-like 样式渲染。不做 PDF.js 完整布局。
- **MD / TXT**：原样渲染（markdown-it）。

v2.0.1+：
- PDF.js 完整页面布局、图片、公式

---

## 7. 复习页（Focus Mode）

### 7.1 进入

- 点左栏底 "🔁 复习 N" 或顶部 "🔁 复习" 按钮
- Focus mode 覆盖整个 shell（fixed 定位），退出按 Esc 或左上 ←

### 7.2 三个状态

**状态 1 · Q 显现**：
- 居中大卡 · 题目 · 元信息（源文档 · 掌握度 · 上次复习时间）
- 提示："先在心里说一遍，再揭示你上次的回答"
- 按钮"显示上次的回答"（`Space` 快捷键）

**状态 2 · A 揭示**：
- Q 保留 + **用户上次的话**（这是 Feynman 关键：复习自己的话，不是标准答案）
- AI 补充点（灰底框）
- 四档评分按钮（again / hard / good / easy）带颜色：
  - 红顶：+1 天
  - 金顶：+3 天
  - 绿顶：+7·(ease+1) 天
  - 蓝顶：+21·(ease+1) 天
- 快捷键 `1 2 3 4`

**状态 3 · 完成**：
- ✓ 统计（N 张通过 / M 张 again）
- 下次复习安排（明天 X 张 · 3 天后 Y 张 · 7 天后 Z 张）
- 返回空间首页

### 7.3 键盘

- `Space` 显示答案
- `1 2 3 4` 评分
- `Esc` 退出

---

## 8. 报告页（v2.0 不改造视觉，延用 v1 逻辑）

报告 prompt 继续沿用 v1 的三段式（已掌握 / 还模糊 / 下周建议），数据源扩展到 v2 新字段：
- 已掌握：本周标 ✓ got_it 的卡 + 用户的话质量（AI 评估） + 覆盖概念
- 还模糊：本周新增 ⚠ stuck + 旧 stuck 没解决 + SM-2 里 again/hard 频率高的卡
- 下周建议：到期卡 · 前置概念补课 · 还没碰过的骨架卡

报告页 UI 先用 v1 的 markdown 渲染方式（pre 或 marked.js），v2.0 不做特殊视觉。

---

## 9. 上传 & 蒸馏进度

状态流：
- `uploading` → 上传到 Supabase Storage
- `parsing` → 解析文档结构
- `chunking` → 分段落
- `embedding` → 批量嵌入（Qwen 限 10/批）
- `distilling_doc` → 生成该文档 summary
- `distilling_space` → 重新蒸馏空间级方向/误解
- `ready` / `failed`

UI：
- 文档卡上显示"蒸馏中..."loader，同时空间级方向/误解卡加灰蒙层提示"正在更新"
- 失败：显示错误 + "重试蒸馏" 按钮

v2.0 UI 简化：文字状态 + 进度条，不做花哨动效。

---

## 10. 配置页（继承 v1，不改）

v2.0 **配置页完全复用 v1 的 ConfigPage**：
- LLM provider + api_key + base_url + model
- Embedding 配置（fallback 到 LLM）
- Supabase URL + service_key

v2.0 新增一个字段：
- `NOTO_DISTILL_MODEL`（可选 · 用于蒸馏的大模型，如果空则用 `ai_model`）

---

## 11. 数据模型

### 11.1 新增表

```sql
skeletons (
  id uuid pk,
  notebook_id uuid not null references notebooks(id) on delete cascade,
  space_summary text,                     -- AI 跨文档合成的空间级概要（3-4 段 markdown）
  generated_at timestamptz default now(),
  status text default 'ready'             -- generating|ready|failed
)
create unique index on skeletons(notebook_id);
-- 说明：一个 skeleton per notebook（空间级聚合）。per-doc 的 summary 存在 documents.summary；这里的 space_summary 是跨文档的空间级概要。

learning_directions (
  id uuid pk,
  skeleton_id uuid references skeletons(id) on delete cascade,
  notebook_id uuid not null,              -- 冗余便于查
  position int,
  title text,
  description text,
  estimated_minutes int
)

skeleton_nodes (
  id uuid pk,
  skeleton_id uuid references skeletons(id) on delete cascade,
  notebook_id uuid not null,
  node_type text,                         -- claim | concept | question | pitfall
  title text,
  body text,
  source_positions jsonb,                 -- [{document_id, chunk_id, page_num}]
  card_source text,                       -- ai_generated | user_selection | user_freeform
  created_at timestamptz default now()
)
-- 一个 node 可以属于多个 direction
create table skeleton_node_directions (
  node_id uuid references skeleton_nodes(id) on delete cascade,
  direction_id uuid references learning_directions(id) on delete cascade,
  primary key (node_id, direction_id)
)

-- 文档级 summary（per-doc）
alter table documents add column summary text;      -- 三段式 markdown
```

### 11.2 改造现有表

```sql
-- cards 表扩字段（继承 v1）
alter table cards add column skeleton_node_id uuid references skeleton_nodes(id) on delete set null;
alter table cards add column card_state text default 'unread';    -- unread|thinking|got_it|stuck
alter table cards add column user_explanation text;                -- 用户自己的话（got_it 才需要）
-- 注：mastery 字段不再使用（v2 不自动打分），移除规划
-- 原文锚点从 skeleton_node 继承（不在 cards 上重复）

-- skeleton_nodes 增 "否决/合并" 支持
alter table skeleton_nodes add column rejected_at timestamptz;           -- 用户否决时间
alter table skeleton_nodes add column rejected_reason text;               -- "不相关" / "重复" / "错误"
alter table skeleton_nodes add column merged_into uuid references skeleton_nodes(id);  -- 合并到哪张卡

-- messages 绑定到 node
alter table messages add column skeleton_node_id uuid references skeleton_nodes(id) on delete cascade;

-- 新增 highlights（选中即高亮存下来）
create table highlights (
  id uuid pk,
  document_id uuid references documents(id) on delete cascade,
  notebook_id uuid not null,
  chunk_id uuid references chunks(id),
  text text,                              -- 选中的原文
  created_at timestamptz default now()
)
```

### 11.3 废弃

- v1 的 `/api/chat/close-conversation` 不是主路径（但保留，用户仍可用）

---

## 12. API 新增/改动

### 12.1 新增路由

- `POST /api/notebooks/{id}/skeleton/regenerate` — 手动触发空间级重新蒸馏
- `GET /api/notebooks/{id}/skeleton` — 拿空间级骨架（directions + nodes + pitfalls）
- `GET /api/documents/{id}/summary` — 文档总结
- `POST /api/documents/{id}/summary/regenerate` — 手动重新蒸馏该文档
- `POST /api/cards/{id}/evaluate` — 提交 user_explanation，AI 返回质性 verdict + feedback（不打分）
- `POST /api/highlights` — 保存高亮
- `POST /api/chat/ask-with-context` — 选中原文段问 AI（跟 `/api/chat/send` 类似但带 selection context）
- `POST /api/skeleton-nodes/{id}/reject` — 用户否决某张骨架卡（软删除 + 记录原因）
- `POST /api/skeleton-nodes/{id}/merge-into` — 把当前卡合并到 target 卡

### 12.2 改动

- 上传 endpoint 返回后，触发的后台任务链变长：parse → chunk → embed → distill_doc_summary → distill_space_skeleton（如果是新增文档）

---

## 13. 简洁约束（硬性）

继承 v1 §10，加上 v2 特有的：

1. **一个空间 = 一套 skeleton**（非 per-doc），避免每份文档都单独一套让用户迷失
2. **跨文档概念不合并**（A 的"链式法则"和 B 的"链式法则"是两张卡，v2.0 不做 embedding-based 归并；v2.1+ 再考虑）
3. **卡片总数硬顶 ≤ 30**，prompt 里明确写死
4. **评判用户"懂了"的 mastery 偏宽松**，≥ 60 通过（用户强制通过兜底）
5. **原文视图不做 PDF.js**，文本 + 页码即可（v2.0.1+ 再升级）
6. **今日建议 · 跨文档自由提问**明确砍掉（避免主页太杂）
7. **AI 评判用独立 prompt**（不复用 Socratic prompt），只评判掌握度
8. **不做暗色模式 / 不做键盘 help 面板 / 不做跨设备同步**（v2.1+）
9. **SSE 协议延用 v1 的 `data: {}\n\n` + `[DONE]`**
10. **Socratic prompt 继承 v1**，扩充一条："对话发生在某张卡的上下文里，不要扯到别的主张"

---

## 14. v2.0 范围（明确做 / 不做）

**v2.0 做**：
- skeletons · skeleton_nodes · learning_directions 三表 + 蒸馏 LLM 调用
- 空间首页新布局（三栏 · 资料/方向/误解 · 右栏知识点）
- 文档阅读视图（summary 顶 + 原文 + 选中浮动工具栏）
- 卡片状态机 + Socratic 追问流（复用 v1 对话管线）
- "懂了"mastery 评判
- 笔记产生 / 锚原文 / 聚合到空间首页
- 复习页 focus mode（新 UI，SM-2 逻辑继承 v1）
- 空间级重新蒸馏（上传新文档时触发）

**v2.0 不做（留 v2.1+）**：
- 跨文档概念合并
- PDF.js 完整渲染
- 代码文件支持（v2.1）
- 仓库分析（v2.2）
- 知识图谱 / 笔记之间 backlinks
- 协作 / 分享
- 移动端适配
- 暗色模式
- 键盘快捷键系统化（只在复习页有基础支持）
- 自定义设计 token 系统 / 用户换肤

---

## 15. 视觉规范

### 15.1 Palette（B 方向 · 温润阅读）

| 变量 | 值 | 用途 |
|---|---|---|
| `--bg` | `#faf7f2` | 主背景（奶油白） |
| `--bg-sidebar` | `#f4efe5` | 左栏 |
| `--bg-drawer` | `#f8f3ea` | 右栏 / 抽屉 |
| `--surface` | `#ffffff` | 卡片主体 |
| `--surface-warm` | `#fdfbf7` | 卡片 hover |
| `--border` | `#e8ddd0` | 分隔线 / 卡边框 |
| `--text` | `#2a2520` | 主文本 |
| `--text-muted` | `#8a7a65` | 次文本 |
| `--text-faint` | `#a89680` | 弱提示 |
| `--accent` | `#c96a3a` | 品牌 / Action |
| `--accent-bg` | `#fbe9d4` | Accent 弱色背景 |
| `--success` | `#6b8a60` | 懂了 / 通过 |
| `--success-bg` | `#dce8d6` | 通过弱色背景 |
| `--highlight` | `#f4e4c1` | 选中/高亮 |

### 15.2 Typography

- 正文 / 标题（衬线）：`'Noto Serif SC', Georgia, serif`
- UI / 元信息 / 按钮（无衬线）：`'Inter', -apple-system, sans-serif`
- logo 直接用真实 SVG/PNG（不用 CSS fallback）

### 15.3 间距 / 圆角

- 卡片圆角 10px（--radius）· 大卡 14px（--radius-lg）· 小 chip 6px（--radius-sm）
- 容器内 padding 16-24px · 卡片内 padding 14-22px
- 主区最大宽度 960-1000px

---

## 16. 从 v1 迁移

- v1 数据表**全部保留**，v2 在其上加字段/新表
- v1 的 notebooks / documents / chunks / conversations / messages / cards / reviews / reports 继续工作
- v2 UI 新建，替换 v1 UI（v1 页面路由删除或重定向到 v2）
- v1 已上传的文档：**需要用户手动触发"蒸馏"**（新增按钮"为已有文档生成骨架"），避免一次性全库重算爆炸 LLM 费用
- 数据迁移：不需要 backfill（v2 字段默认 null，蒸馏后填入）

---

## 17. 里程碑切分（供 writing-plans 参考）

**M1 · 后端蒸馏管线**：
- skeletons / learning_directions / skeleton_nodes 三表 + 迁移
- distill_doc_summary prompt + 调用
- distill_space_skeleton prompt + 调用（含硬顶 30 张卡的约束）
- 新 API routes
- `cards` 表字段扩展 + mastery 评判 endpoint

**M2 · 空间首页 + 文档阅读**：
- 三栏布局 shell
- 空间首页（正方形文档卡 + 学习方向 + 误解）
- 右栏"我的知识点"（简单列表，"按主题 ▾" 下拉 v2.0 只做按状态分组：got_it / thinking / stuck）
- 文档阅读视图（summary + 原文 + 选中浮动工具栏）
- highlights 表 + 保存高亮 API
- 上传流 + 状态 UI

**M3 · 卡片交互 + 复习**：
- 方向展开视图
- 卡片 Socratic 追问流（展开/收起/状态机）
- "懂了"modal + mastery 评判（用 M1 的 API）
- 复习页 focus mode
- 报告页视觉微调（内容不变）

每个里程碑可独立 demo。
