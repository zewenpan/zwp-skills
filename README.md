# zwp-skills

按**粗粒度功能类别**组织的 skill 集合（自用 + 精选第三方），便于未来对同一类别下的技能做**横向评估**。

This is **zwp-skills**, reorganized into coarse functional folders for transversal evaluation across skills in the same category.

每个叶子目录都是独立可拷贝的 skill —— 把 `skills/<类别>/.../<skill>`（或更深路径）拷进你的 skill 目录即可。

> **brooks-test**：使用 **xav 定制版**（含 `test-guide.md`），覆盖 brooks-lint 上游同名技能。
>
> **matt-pocock-skills**：保留原 pack 嵌套 `engineering/` + `productivity/`。
>
> **anthropics**：合在一个 pack 下，再按功能分子目录（`ui-design` / `documents` / `api` / `meta`）。
>
> **language**：语言类（表达风格 / 对齐用户预期），当前仅收录 `i-have-adhd`。
>
> **xav**：仅 `copilot-jev-flagship`、`jev-api`。

## 目录结构 / Tree

```
skills/
  matt-pocock-skills/   # Matt Pocock pack；内嵌 engineering + productivity
    engineering/       # 工程流：规格、实现、评审、排障、路由等
    productivity/      # 生产力：追问、交接、教学、为 agent 写作等
  brooks-lint/         # 代码健康套件（_shared + brooks-*；brooks-test = xav 覆盖）
  ui-ux-pro-max/       # UI/UX、品牌、设计系统、幻灯片、样式
  anthropics/          # Anthropic skills，按功能再分桶
    ui-design/         # 前端与视觉设计、主题、算法艺术、GIF
    documents/         # docx/pdf/pptx/xlsx、共写文档、内部沟通
    api/               # Claude API、MCP builder、webapp-testing
    meta/              # skill-creator、academy-guide、discernment-nudge
  xav/                 # 自用 API：copilot-jev-flagship、jev-api
  language/            # 语言类：对齐表达风格（i-have-adhd）
```

机器可读类别映射见 [`skills/CATEGORIES.md`](skills/CATEGORIES.md)。

## 怎么装 / Install

```bash
git clone https://github.com/zewenpan/zwp-skills.git
# 拷贝某个叶子 skill（路径可能更深）
cp -r zwp-skills/skills/<category>/.../<skill> ~/.workbuddy/skills/
# 例：
cp -r zwp-skills/skills/matt-pocock-skills/engineering/tdd ~/.workbuddy/skills/
cp -r zwp-skills/skills/brooks-lint/brooks-test ~/.workbuddy/skills/
cp -r zwp-skills/skills/language/i-have-adhd ~/.workbuddy/skills/
cp -r zwp-skills/skills/xav/jev-api ~/.workbuddy/skills/
```

## Skills（62，按类别）

### matt-pocock-skills / engineering

Matt Pocock 工程流：规格、实现、评审、排障、路由等。Keep pack nesting for engineering.

| Skill | 一句话 / Description |
|---|---|
| [`ask-matt`](skills/matt-pocock-skills/engineering/ask-matt/) | Ask which skill or flow fits your situation. A router over the skills in this repo. |
| [`code-review`](skills/matt-pocock-skills/engineering/code-review/) | Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes: Standards (does the code follow this repo's d... |
| [`codebase-design`](skills/matt-pocock-skills/engineering/codebase-design/) | Shared vocabulary for designing deep modules. Use when the user wants to design or improve a module's interface, find deepening opportuni... |
| [`diagnosing-bugs`](skills/matt-pocock-skills/engineering/diagnosing-bugs/) | Diagnosis loop for hard bugs and performance regressions. Use when the user says "diagnose"/"debug this", or reports something broken/thr... |
| [`domain-modeling`](skills/matt-pocock-skills/engineering/domain-modeling/) | Build and sharpen a project's domain model. Use when discussing codebase terminology, writing or editing a GLOSSARY.md, or recording or e... |
| [`grill-with-docs`](skills/matt-pocock-skills/engineering/grill-with-docs/) | A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go. |
| [`implement`](skills/matt-pocock-skills/engineering/implement/) | Implement a piece of work based on a spec or set of tickets. |
| [`implement-spec`](skills/matt-pocock-skills/engineering/implement-spec/) | Implement the result of /to-spec and /to-tickets in code. |
| [`improve-codebase-architecture`](skills/matt-pocock-skills/engineering/improve-codebase-architecture/) | Scan a codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick. |
| [`pr`](skills/matt-pocock-skills/engineering/pr/) | Use when writing a PR body. |
| [`prototype`](skills/matt-pocock-skills/engineering/prototype/) | Build a throwaway prototype to answer a design question. Use when the user wants to sanity-check whether a state model or logic feels rig... |
| [`research`](skills/matt-pocock-skills/engineering/research/) | Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user want... |
| [`retro`](skills/matt-pocock-skills/engineering/retro/) | Conduct a retrospective on a coding session. |
| [`setup-matt-pocock-skills`](skills/matt-pocock-skills/engineering/setup-matt-pocock-skills/) | Configure this repo for the engineering skills: set up its issue tracker, triage label vocabulary, and domain doc layout. Run once before... |
| [`tdd`](skills/matt-pocock-skills/engineering/tdd/) | Test-driven development. Use when the user wants to build features or fix bugs test-first, mentions "red-green-refactor", or wants integr... |
| [`to-spec`](skills/matt-pocock-skills/engineering/to-spec/) | Turn the current conversation into a spec and publish it to the project issue tracker: no interview, just synthesis of what you've alread... |
| [`to-tickets`](skills/matt-pocock-skills/engineering/to-tickets/) | Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the ... |
| [`triage`](skills/matt-pocock-skills/engineering/triage/) | Move issues and external PRs through a state machine of triage roles, categorise, verify, grill if needed, and write agent-ready briefs. |
| [`wayfinder`](skills/matt-pocock-skills/engineering/wayfinder/) | Plan a huge chunk of work (more than one agent session can hold) as a shared map of decision tickets on your issue tracker, and resolve t... |
| [`wizard`](skills/matt-pocock-skills/engineering/wizard/) | Generate an interactive bash wizard that walks a human through steps only they can perform. Use when provisioning infrastructure, setting... |

### matt-pocock-skills / productivity

Matt Pocock 生产力：追问、交接、教学、为 agent 写作等。

| Skill | 一句话 / Description |
|---|---|
| [`grill-me`](skills/matt-pocock-skills/productivity/grill-me/) | A relentless interview to sharpen a plan or design. |
| [`grilling`](skills/matt-pocock-skills/productivity/grilling/) | Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' t... |
| [`handoff`](skills/matt-pocock-skills/productivity/handoff/) | Compact the current conversation into a handoff document for another agent to pick up. |
| [`teach`](skills/matt-pocock-skills/productivity/teach/) | Teach the user a new skill or concept, within this workspace. |
| [`to-questionnaire`](skills/matt-pocock-skills/productivity/to-questionnaire/) | Turn a decision you can't fully answer into a questionnaire for someone else to fill in. |
| [`wait-what`](skills/matt-pocock-skills/productivity/wait-what/) | Stop. That last message did not land: re-pitch it. |
| [`writing-for-agents`](skills/matt-pocock-skills/productivity/writing-for-agents/) | Writing documents for agents. Use when creating or editing skills, or modifying AGENTS.md or CLAUDE.md. |

### brooks-lint

代码健康 / lint 审计套件。`brooks-test` 为 **xav 定制版**（含 `test-guide.md`），覆盖上游。

| Skill | 一句话 / Description |
|---|---|
| [`brooks-audit`](skills/brooks-lint/brooks-audit/) | Architecture audit that maps module dependencies, checks layering integrity, and flags structural decay across a codebase, drawing on twe... |
| [`brooks-debt`](skills/brooks-lint/brooks-debt/) | Tech debt assessment that identifies, classifies, and prioritizes maintainability problems — helping teams build a refactoring roadmap — ... |
| [`brooks-health`](skills/brooks-lint/brooks-health/) | Combined codebase health dashboard that scores a project across all four quality dimensions — PR quality, architecture, tech debt, and te... |
| [`brooks-review`](skills/brooks-lint/brooks-review/) | PR code review that surfaces decay risks, design smells, and maintainability issues with concrete Symptom → Source → Consequence → Remedy... |
| [`brooks-sweep`](skills/brooks-lint/brooks-sweep/) | Full-sweep mode: runs a unified analysis across all quality dimensions — code decay, architecture, tech debt, and test quality — then app... |
| [`brooks-test`](skills/brooks-lint/brooks-test/) | Reviews and rebuilds test suites against three golden standards — tests never reshape production code, tests assert observable behavior, ... |

### ui-ux-pro-max

UI/UX、品牌、设计系统、幻灯片与样式。

| Skill | 一句话 / Description |
|---|---|
| [`banner-design`](skills/ui-ux-pro-max/banner-design/) | Design banners for social media, ads, website heroes, creative assets, and print. Multiple art direction options with optional generated ... |
| [`brand`](skills/ui-ux-pro-max/brand/) | Brand voice, visual identity, messaging frameworks, asset management, brand consistency. Activate for branded content, tone of voice, mar... |
| [`design`](skills/ui-ux-pro-max/design/) | Comprehensive design skill: brand identity, design tokens, UI styling, logo generation (55 styles, Gemini, Atlas Cloud, or MuAPI AI), cor... |
| [`design-system`](skills/ui-ux-pro-max/design-system/) | Token architecture, component specifications, and slide generation. Three-layer tokens (primitive→semantic→component), CSS variables, spa... |
| [`slides`](skills/ui-ux-pro-max/slides/) | Create strategic HTML presentations with Chart.js, design tokens, responsive layouts, copywriting formulas, and contextual slide strategies. |
| [`ui-styling`](skills/ui-ux-pro-max/ui-styling/) | Create beautiful, accessible user interfaces with shadcn/ui components (built on Radix UI + Tailwind), Tailwind CSS utility-first styling... |
| [`ui-ux-pro-max`](skills/ui-ux-pro-max/ui-ux-pro-max/) | UI/UX design intelligence for web, mobile, and desktop. This skill should be used when designing, building, reviewing, or fixing interfac... |

### anthropics / ui-design

前端与视觉设计、主题、算法艺术、Slack GIF 等。

| Skill | 一句话 / Description |
|---|---|
| [`algorithmic-art`](skills/anthropics/ui-design/algorithmic-art/) | Creating algorithmic art using p5.js with seeded randomness and interactive parameter exploration. Use this when users request creating a... |
| [`brand-guidelines`](skills/anthropics/ui-design/brand-guidelines/) | Applies Anthropic's official brand colors and typography to any sort of artifact that may benefit from having Anthropic's look-and-feel. ... |
| [`canvas-design`](skills/anthropics/ui-design/canvas-design/) | Create beautiful visual art in .png and .pdf documents using design philosophy. You should use this skill when the user asks to create a ... |
| [`frontend-design`](skills/anthropics/ui-design/frontend-design/) | Guidance for distinctive, intentional visual design when building new UI or reshaping an existing one. Helps with aesthetic direction, ty... |
| [`slack-gif-creator`](skills/anthropics/ui-design/slack-gif-creator/) | Knowledge and utilities for creating animated GIFs optimized for Slack. Provides constraints, validation tools, and animation concepts. U... |
| [`theme-factory`](skills/anthropics/ui-design/theme-factory/) | Toolkit for styling artifacts with a theme. These artifacts can be slides, docs, reportings, HTML landing pages, etc. There are 10 pre-se... |
| [`web-artifacts-builder`](skills/anthropics/ui-design/web-artifacts-builder/) | Suite of tools for creating elaborate, multi-component claude.ai HTML artifacts using modern frontend web technologies (React, Tailwind C... |

### anthropics / documents

Office 文档（docx/pdf/pptx/xlsx）、共写文档、内部沟通。

| Skill | 一句话 / Description |
|---|---|
| [`doc-coauthoring`](skills/anthropics/documents/doc-coauthoring/) | Guide users through a structured workflow for co-authoring documentation. Use when user wants to write documentation, proposals, technica... |
| [`docx`](skills/anthropics/documents/docx/) | Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx files) or Word templates (.dotx files).... |
| [`internal-comms`](skills/anthropics/documents/internal-comms/) | A set of resources to help me write all kinds of internal communications, using the formats that my company likes to use. Claude should u... |
| [`pdf`](skills/anthropics/documents/pdf/) | Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combinin... |
| [`pptx`](skills/anthropics/documents/pptx/) | Use this skill any time a .pptx or .potx file is involved in any way — as input, output, or both. This includes: creating slide decks, pi... |
| [`xlsx`](skills/anthropics/documents/xlsx/) | Use this skill any time a spreadsheet file is the primary input or output. This means any task where the user wants to: open, read, edit,... |

### anthropics / api

Claude API、MCP builder、webapp-testing（Playwright）。

| Skill | 一句话 / Description |
|---|---|
| [`claude-api`](skills/anthropics/api/claude-api/) | Reference for the Claude API / Anthropic SDK — model ids, pricing, params, streaming, tool use, MCP, agents, caching, token counting, mod... |
| [`mcp-builder`](skills/anthropics/api/mcp-builder/) | Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-des... |
| [`webapp-testing`](skills/anthropics/api/webapp-testing/) | Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI... |

### anthropics / meta

技能创作与元指导。

| Skill | 一句话 / Description |
|---|---|
| [`academy-guide`](skills/anthropics/meta/academy-guide/) | Stop and check this skill before finishing any reply to a question about how to use Claude or a Claude product — it recommends matching c... |
| [`discernment-nudge`](skills/anthropics/meta/discernment-nudge/) | After you give a substantive answer or draft that the user may act on — advice or recommendations, drafted artifacts such as goals, plans... |
| [`skill-creator`](skills/anthropics/meta/skill-creator/) | Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch,... |

### xav

自用 API / Copilot：`copilot-jev-flagship`、`jev-api`。

| Skill | 一句话 / Description |
|---|---|
| [`copilot-jev-flagship`](skills/xav/copilot-jev-flagship/) | 内领旗舰版 Copilot Jev / System One 极简调用技能。需要用本人 pt_ 开头的 Copilot JWT 对一段文本或 JSON 做 noul、choice、score 判断，或排查 /v2/systemone 的 11102、401 等错误时使用。 |
| [`jev-api`](skills/xav/jev-api/) | TypeSafe Jev(System One,社区口头叫 "jav")的最小可用 API 手册与零依赖客户端——只填一个环境变量 TYPESAFE_API_KEY 就能直接调用,不需要读官方文档。当任务需要给文本/对象做结构化判定:分类、打标、路由、多档打分、是/否门控、... |

### language

语言类：让回答更对齐用户预期与表达风格（当前仅收录 `i-have-adhd`）。

| Skill | 一句话 / Description |
|---|---|
| [`i-have-adhd`](skills/language/i-have-adhd/) | Shape output for a reader with ADHD: lead with the next action, number multi-step work, restate state across turns, suppress tangents, gi... |

