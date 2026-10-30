# zwp-skills

My self-made skill collection.

每个目录都是独立的、可单独下载使用的 skill —— 拷进你的 skill 目录即可,不需要读额外的文档。

## Skills

| Skill | 一句话 | 依赖 |
|---|---|---|
| [`brooks-test`](skills/brooks-lint-xav/brooks-test/) | Brooks Lint / XAV 相关测试与校验指引 | 见 SKILL.md |
| [`copilot-jev-flagship`](skills/copilot-jev-flagship/) | 内领旗舰版 Copilot Jev / System One 极简调用（`pt_` JWT） | 见 SKILL.md / `scripts/jev.py` |
| [`jev-api`](skills/jev-api/) | TypeSafe Jev(System One / "jav")的最小 API 手册 + 零依赖客户端。**只填一个环境变量 `TYPESAFE_API_KEY` 就能用** | 无(仅 Python 标准库) |

## 怎么装

**WorkBuddy / CodeBuddy 用户** —— 把 skill 目录拷到用户级 skills 目录即可全局可用:

```bash
git clone https://github.com/zewenpan/zwp-skills.git
cp -r zwp-skills/skills/jev-api ~/.workbuddy/skills/          # macOS / Linux
xcopy /E /I zwp-skills\skills\jev-api %USERPROFILE%\.workbuddy\skills\jev-api   # Windows
```

同理可拷贝 `skills/copilot-jev-flagship`、`skills/brooks-lint-xav/brooks-test`。

**其它 Agent / 只想直接跑** —— 不用装。例如 `skills/jev-api/scripts/jev.py` 是零依赖的单文件客户端,拷走就能用:

```bash
python jev.py --selftest
```

**只想抄请求格式** —— 看对应 skill 的 `SKILL.md`;`jev-api` 还可看 `reference/cookbook.md`。

## 设计约定

- **一个 skill 只解决一件事**,边界写进 `SKILL.md` 的 description。
- **零依赖优先**。能用标准库就不引第三方包 —— 下载即用比功能齐全重要。
- **文档不漂移**。所有数字与契约都来自真实调用,可被 `tests/` 重放校验;拿不到实测数据的话,不写。
- **每个 skill 自带验证入口**。`--selftest`(要 key)或 `tests/`(不需要 key)。

## License

MIT
