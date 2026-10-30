# zwp-skills

My self-made skill collection.

每个目录都是独立的、可单独下载使用的 skill —— 拷进你的 skill 目录即可,不需要读额外的文档。

## Skills

| Skill | 一句话 | 依赖 |
|---|---|---|
| [`banner-design`](skills/banner-design/) | Design banners for social media, ads, website heroes, creative assets, and print. Multiple art direction options with optional generated or  | 见 SKILL.md |
| [`brand`](skills/brand/) | Brand voice, visual identity, messaging frameworks, asset management, brand consistency. Activate for branded content, tone of voice, market | 见 SKILL.md |
| [`brooks-lint-xav/brooks-test`](skills/brooks-lint-xav/brooks-test/) | > | 见 SKILL.md |
| [`copilot-jev-flagship`](skills/copilot-jev-flagship/) | 内领旗舰版 Copilot Jev / System One 极简调用技能。需要用本人 pt_ 开头的 Copilot JWT 对一段文本或 JSON 做 noul、choice、score 判断，或排查 /v2/systemone 的 11102、401 等错误时使用。 | 见 SKILL.md |
| [`design`](skills/design/) | Comprehensive design skill: brand identity, design tokens, UI styling, logo generation (55 styles, Gemini, Atlas Cloud, or MuAPI AI), corpor | 见 SKILL.md |
| [`design-system`](skills/design-system/) | Token architecture, component specifications, and slide generation. Three-layer tokens (primitive→semantic→component), CSS variables, spacin | 见 SKILL.md |
| [`i-have-adhd`](skills/i-have-adhd/) | Shape output for a reader with ADHD: lead with the next action, number multi-step work, restate state across turns, suppress tangents, give  | 见 SKILL.md |
| [`jev-api`](skills/jev-api/) | TypeSafe Jev(System One,社区口头叫 "jav")的最小可用 API 手册与零依赖客户端——只填一个环境变量 TYPESAFE_API_KEY 就能直接调用,不需要读官方文档。当任务需要给文本/对象做结构化判定:分类、打标、路由、多档打分、是/否门控、分诊、 | 见 SKILL.md |
| [`slides`](skills/slides/) | Create strategic HTML presentations with Chart.js, design tokens, responsive layouts, copywriting formulas, and contextual slide strategies. | 见 SKILL.md |
| [`ui-styling`](skills/ui-styling/) | Create beautiful, accessible user interfaces with shadcn/ui components (built on Radix UI + Tailwind), Tailwind CSS utility-first styling, a | 见 SKILL.md |
| [`ui-ux-pro-max`](skills/ui-ux-pro-max/) | UI/UX design intelligence for web, mobile, and desktop. This skill should be used when designing, building, reviewing, or fixing interfaces, | 见 SKILL.md |

## 怎么装

**WorkBuddy / CodeBuddy / Cursor 等** —— 把对应 skill 目录拷到用户级 skills 目录即可全局可用:

```bash
git clone https://github.com/zewenpan/zwp-skills.git
cp -r zwp-skills/skills/<skill-name> ~/.workbuddy/skills/
```

## 设计约定

- **一个 skill 只解决一件事**,边界写进 `SKILL.md` 的 description。
- **零依赖优先**。能用标准库就不引第三方包 —— 下载即用比功能齐全重要。
- **文档不漂移**。拿不到实测数据的话,不写。
- **每个 skill 自带验证入口**（如有）。

## License

MIT
