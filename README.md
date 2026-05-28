<div align="center">

# project_map

**Code Index Tool for AI Coding Assistants · 给 AI 编程助手的代码索引工具**

60–95% fewer search tokens in typical use · 典型场景节省 60–95% 的搜索 token

</div>

---

[English](#english) · [中文](#中文)

---

## English

### What is this

`map.py` is a local code-indexing script designed for AI coding assistants like Claude Code and Codex.

When an AI assistant investigates a bug, it typically searches through source directories — dumping hundreds of matching lines into context and burning through tokens. `project_map` pre-indexes your project's symbols (functions, components, classes) so the AI can query the index instead of scanning raw source, dramatically reducing output volume.

### Prerequisites

- Python 3.8+
- Claude Code, Codex, Cursor, or any AI coding assistant that supports `CLAUDE.md` / `AGENTS.md` rule files

> **Note:** `CLAUDE.md` is written for Claude Code. For Cursor, Codex, or other frameworks, just copy the contents of `CLAUDE.md` into that framework's rule file (e.g. `AGENTS.md`).

### Installation

#### Automatic (recommended)

```bash
python3 install.py /path/to/your-project
```

The script will:
1. Copy `map.py` to the target project's root directory
2. Write the usage rules into the target project's `CLAUDE.md` (appends if it exists, creates if it doesn't)
3. Add `.project-index/` to `.gitignore` (appends if it exists, creates if it doesn't)
4. Run `map.py` once to generate the initial index

#### Manual

1. Copy `map.py` to your project root
2. Paste the contents of this repo's `CLAUDE.md` into your project's `CLAUDE.md` (create it if it doesn't exist)
3. Add `.project-index/` to your `.gitignore`

### How it works

Queries complete in three hops:

1. **Hop 1 — Small map**: search `.project-index/project-map.json` to find which files contain the target symbol
2. **Hop 2 — Bucket index**: search the detailed index for the matching file type, e.g. `.project-index/jsx/code-index.json`
3. **Hop 3 — Candidate files**: open only the most relevant matched files, up to 10

Each hop's output is far smaller than a raw source scan, resulting in significantly lower token usage.

### Why it doesn't consume AI tokens

Every step of `project_map` — building the index, querying the index — runs without calling any AI:

- `map.py` is a plain Python script that extracts symbol names using regex and syntax parsing, with no model calls
- The generated index is a set of static JSON files stored on local disk
- When the AI queries the index, it runs `rg` against JSON files — no vector embeddings, no model inference

Other memory and indexing tools typically spend AI tokens on content compression, vector embedding, or semantic understanding. `project_map` bypasses all of that entirely. Building and querying the index costs **zero AI tokens**.

The token savings come entirely from "AI reads a small JSON instead of scanning large source files" — not from spending tokens to save tokens.

### The static index is not a limitation

The index is refreshed automatically at the start of each session (see `CLAUDE.md` rules). Refreshing just means running `map.py` — no token cost.

During a session, any files the AI has already opened or edited are present in the conversation context. The AI already knows what changed. The index is only needed to locate files the AI hasn't opened yet, so there's no "stale index" problem mid-session.

There's also a fallback: if the index produces no results, `map.py` is re-run once before falling back to direct source search.

### Index structure

Running `map.py` generates the following layout:

```
.project-index/
├── project-map.json        # Small map: symbol summary for the whole project (hop 1)
├── jsx/
│   └── code-index.json     # Detailed index for JSX files
├── js/
│   └── code-index.json     # Detailed index for JS files
├── java/
│   └── code-index.json     # Detailed index for Java files
├── ts/
│   └── code-index.json
└── ...                     # One bucket per file extension
```

Buckets exist so that a frontend query only loads the `jsx/js/ts` bucket and a backend query only loads the `java` bucket — no need to load the full index, which keeps output size small.

### Supported file types

**Code**: `.ts` `.tsx` `.js` `.jsx` `.mjs` `.cjs` `.py` `.java` `.vue` `.svelte`

**Config / support files**: `.css` `.html` `.json` `.xml` `.yaml` `.yml` `.properties` `.sql` `.md`

### Skeptical about the token savings?

Good. You're encouraged to challenge it.

Just tell the AI something like: *"Prove that the map saves tokens — run a comparison."*

The AI will then run the same lookup twice on a real task:

- **With map**: three-hop query through the index, records token count
- **Without map**: direct keyword search in the source directory, records token count
- **Result**: savings rate = `(without − with) / without`

The comparison is run on a real task in the current session, so the numbers reflect your actual project. Note that running the "without map" control search itself wastes tokens — it exists only to answer your challenge, not as part of normal operation.

---

## 中文

### 这是什么

`map.py` 是一个本地代码索引脚本，专为 Claude Code、Codex 等 AI 编程助手设计。

AI 助手排查问题时，通常需要在源码目录里搜索——每次搜索会把大量匹配行塞进上下文，消耗大量 token。`project_map` 的做法是：提前把项目里的函数名、组件名、类名等符号建成索引，AI 查索引代替直接扫源码，大幅压缩输出体积。

### 前提条件

- Python 3.8+
- Claude Code、Codex、Cursor 或其他支持 `CLAUDE.md` / `AGENTS.md` 规则文件的 AI 编程助手

> **注意**：本仓库的 `CLAUDE.md` 是为 Claude Code 编写的规则文件。用于 Cursor、Codex 等其他框架时，把 `CLAUDE.md` 的内容直接复制到该框架对应的规则文件里即可（如 `AGENTS.md`）。

### 安装

#### 自动安装（推荐）

```bash
python3 install.py /path/to/your-project
```

脚本会：
1. 把 `map.py` 复制到目标项目根目录
2. 把使用规则写入目标项目的 `CLAUDE.md`（已有则追加，没有则新建）
3. 把 `.project-index/` 写入 `.gitignore`（已有则追加，没有则新建）
4. 自动运行 `map.py` 生成初始索引

#### 手动安装

1. 复制 `map.py` 到你的项目根目录
2. 把本仓库 `CLAUDE.md` 的内容粘贴到你项目的 `CLAUDE.md` 末尾（没有则新建）
3. 把 `.project-index/` 加入 `.gitignore`

### 工作原理

查询分三跳完成：

1. **第一跳 — 小地图**：搜 `.project-index/project-map.json`，确认哪些文件包含目标符号
2. **第二跳 — 分桶索引**：搜对应格式的详细索引，如 `.project-index/jsx/code-index.json`
3. **第三跳 — 候选文件**：只读最相关的候选文件，最多 10 个

每跳的输出体积远小于直接扫源码，token 消耗大幅下降。

### 为什么不消耗 AI token

`project_map` 的整个流程——生成索引、查询索引——没有任何步骤调用 AI：

- `map.py` 是纯 Python 脚本，用正则和语法解析提取符号名，不调用任何模型
- 生成的索引是静态 JSON 文件，存在本地磁盘
- AI 查索引时用的是 `rg` 在 JSON 文件里做关键词匹配，不需要向量嵌入或模型推理

对比其他同类记忆/索引外挂，通常需要用 AI token 来做内容压缩、向量嵌入或语义理解；`project_map` 完全绕开了这条路，索引本身的生成和查询**零 token 消耗**。

节省的 token 全部来自"AI 读小 JSON 代替扫大量源码文件"，不是靠花 token 来省 token。

### 静态索引不是缺陷

索引在每次会话开始时自动更新一次（见 `CLAUDE.md` 规则），更新本身只是跑 `map.py` 脚本，不耗费 token。

会话过程中如果修改了某些文件，这些改动已经在当次对话的上下文里，AI 直接知道改了什么，不需要索引来告诉它——**索引只用于定位 AI 还没打开的文件**。所以会话中途不需要重跑 `map.py`，静态索引在这个使用场景下不存在"过期"问题。

另外，`CLAUDE.md` 里还有兜底措施：如果地图定位失败，先重新生成索引再查一次，仍然失败才降级到直接搜源码。

### 索引结构

运行 `map.py` 后会生成以下结构：

```
.project-index/
├── project-map.json        # 小地图：全项目符号摘要，第一跳在这里查
├── jsx/
│   └── code-index.json     # JSX 文件详细索引
├── js/
│   └── code-index.json     # JS 文件详细索引
├── java/
│   └── code-index.json     # Java 文件详细索引
├── ts/
│   └── code-index.json
└── ...                     # 按文件后缀分桶，每种格式独立一个桶
```

按后缀分桶的原因：排查前端问题只需查 `jsx/js/ts` 桶，排查后端只需查 `java` 桶，不必加载全量索引，进一步缩小输出体积。

### 支持的文件类型

**代码文件**：`.ts` `.tsx` `.js` `.jsx` `.mjs` `.cjs` `.py` `.java` `.vue` `.svelte`

**配置/支撑文件**：`.css` `.html` `.json` `.xml` `.yaml` `.yml` `.properties` `.sql` `.md`

### 对 token 节省效果有疑问？

欢迎质疑，直接说就行。

告诉 AI 类似：*「证明地图能省 token，跑一次对比」*

AI 会针对当前会话里的一个真实任务跑两遍：

- **用地图**：三跳索引查询，记录 token 数
- **不用地图**：直接搜源码目录，记录 token 数
- **结果**：节省率 = `(不用地图 − 用地图) / 不用地图`

对比基于你的真实项目和真实任务，数据有实际意义。注意：跑「不用地图」那遍本身会浪费 token，只在你提出质疑时才跑，平时正常使用不会有这一步。
