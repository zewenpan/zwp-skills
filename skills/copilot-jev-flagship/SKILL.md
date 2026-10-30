---
name: copilot-jev-flagship
description: 内领旗舰版 Copilot Jev / System One 极简调用技能。需要用本人 pt_ 开头的 Copilot JWT 对一段文本或 JSON 做 noul、choice、score 判断，或排查 /v2/systemone 的 11102、401 等错误时使用。
agent_created: true
---

# 内领旗舰版 · Jev

仅需一枚本人获授权的 Copilot 凭据，即可调用 Jev 的同步判断接口。脚本只使用 Python 3 标准库，不安装依赖。

## 先认对钥匙

| 凭据 | 形状 | 本技能用途 |
| --- | --- | --- |
| **Copilot JWT / 会话令牌** | **`pt_...`** | **使用这一种。** 虽在本环境称为 JWT，实际不一定是三段式 JWT；原样作为 Bearer 发送。 |
| Copilot Key | `ck_...` | **不要用**；实测请求 Jev 返回 `11102: model [jev] is not served by route v3`。 |
| TypeSafe API Key | `apikey_...` | 仅用于另一套 TypeSafe 原生 `/v1/systemone`，协议不同。 |

只接受用户本人提供的 `pt_` 凭据；不得从应用缓存抓取、复用他人令牌、伪造他人的用户或租户 ID。不要把令牌写入 SKILL.md、脚本、命令参数、日志或产物。优先在终端隐式输入，或者使用用户**明确指定**的 `jwt=pt_...` 本地文件。

## 一步跑通

在技能目录执行：

```bash
python3 scripts/jev.py
```

在隐藏输入提示处粘贴 `pt_...`，回车。脚本用一张“发票错误，今天需要帮助”的示例工单，自动问三题：是/否（`noul`）、归属团队（`choice`）、紧急程度（`score`）。本地文件中已有 `jwt=...` 时，可避免交互：

```bash
python3 scripts/jev.py --env-file /绝对路径/.env
```

如需替换判断材料和问题，准备 UTF-8 JSON 文件，仅包含 `state` 与 `questions`，再执行 `python3 scripts/jev.py --env-file /绝对路径/.env --input /绝对路径/case.json`。其中一个最小案例为 `{"state":"用户今天需要发票帮助","questions":{"urgent":{"instructions":"是否需要今天处理？","noul":{}}}}`。每个问题只能选 `noul: {}`、`choice: {"criteria": {"键":"描述"}}`、`score: {"criteria": ["低","高"]}` 之一；问题的 key 仅用于匹配答案，真正意图写进 `instructions`。

## 最小协议和验收

- 固定 `POST https://copilot.tencent.com/v2/systemone`；`Authorization: Bearer pt_...`、`Content-Type: application/json`，以及 `X-Conversation-ID`、`X-Conversation-Request-ID`、`X-Conversation-Message-ID`、`User-Agent`、`X-IDE-Type`、`X-IDE-Name` 六个请求头。脚本自动生成请求 ID，IDE 均为 `vscode`。
- 请求体为 `{"model":"jev","stream":false,"system_one":{"state":...,"questions":...}}`。`stream` 必须为 `false`；不可套 TypeSafe 的平铺格式。
- 仅在 **HTTP 200 且 `type=systemone.answers.done`、`model=jev`、`answers` 为对象**时报告成功。`noul` 返回“是”的概率；`choice` 返回选项键及概率；`score` 返回量表落点和档位概率；`usage` 包含 token 用量。脚本直接输出响应 JSON，不输出令牌。
- `11102`：先确认是否误拿 `ck_`，再核对权限与模型路由；`11101`：检查请求头、`stream=false` 和题目形状；`401/403`：确认 `pt_` 是否有效及本人是否具备权限。**无需**复制 `model-train`、SaaS、B3 trace 或他人的用户/租户头；最小头组合已实测 HTTP 200。
