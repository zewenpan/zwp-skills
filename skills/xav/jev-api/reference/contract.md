# Jev API 完整契约参考

> 本文件是 `SKILL.md` 的深水区。日常用不到 —— 需要抠字段语义、排错误码、算成本时才翻。
> 所有数字均为 **2026-09-20 本机真实调用实测**(`jev-1.13.0`),不是文档转述。

---

## 1. 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `https://api.typesafe.ai/v1/systemone` | 唯一的主接口 |
| `GET` | `https://api.typesafe.ai/v1/models` | 列出可用模型 |
| `GET` | `https://api.typesafe.ai/health` | 健康检查,返回 `ok` |
| — | `/v1/chat/completions` | **不存在(404)**。它不是聊天模型 |

认证:`Authorization: Bearer <API_KEY>`。国内可直连,通常无需代理。

---

## 2. 请求字段

```
{ "state": <string|object|array>, "model": <string>, "questions": { <id>: <question> } }
```

### 2.1 `state`

- `string`:最常用。中文无退化(本次全部场景都是中文 state + 中文 criteria)
- `object` / `array`:结构化输入。要在 `instructions` 里引用其中某个键时,用**反引号**包住键名,例如:

  ```json
  {
    "state": {"A1": "自动整理会议纪要的工具", "A2": "宠物零食盲盒电商"},
    "questions": {
      "A1": {"type": "score", "instructions": "`A1` 这个方向作为独立产品的商业可行性?", "criteria": ["很差","较差","一般","不错","很好"]},
      "A2": {"type": "score", "instructions": "`A2` 这个方向作为独立产品的商业可行性?", "criteria": ["很差","较差","一般","不错","很好"]}
    }
  }
  ```

  这是**批量打分排序**的惯用法:一次调用给 N 个候选各自打分,再在本地排序。

### 2.2 `model`

| 值 | 行为 |
|---|---|
| `jev-latest` | 滚动到最新。推荐 |
| `jev-preview` | 预览通道(实测与 latest 同解析到 `jev-1.13.0`) |
| `jev-1.13.0` | 固定版本,用于要求可复现的生产 |
| 其它任意字符串 | `400 Unknown model` —— **不会静默降级** |

### 2.3 `questions.<id>`

`id` 由你命名,会原样回显在 `answers` 里,所以**命名即接口** —— 建议用代码里直接消费的名字(`route` / `verdict` / `need_human`)。

| 字段 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `type` | 是 | `"choice"` \| `"score"` \| `"noul"` | 其它值 → `400 api_usage_error` |
| `instructions` | 是 | string | 自然语言问法。可内嵌 dict/list 结构数据,用反引号引用 |
| `criteria` | `choice`/`score` 必填 | dict / list | 见下 |
| 额外字段 | — | — | 实测传多余字段不影响(会被忽略) |

**`criteria` 的两种形态,决定返回值形态:**

```jsonc
// dict —— key 就是返回值,value 是给模型看的判别说明
"criteria": { "tiny": "微型模型:格式化/翻译等确定性改写",
              "small": "小模型:单文件代码改动",
              "mid":   "中档模型:多文件重构",
              "frontier": "前沿模型:长链推理/架构设计" }
// -> answers[id].choice 一定是 "tiny"|"small"|"mid"|"frontier" 之一

// list —— 有序刻度,返回**下标**(0..n-1,浮点)
"criteria": ["平静", "轻微不悦", "明显不满", "愤怒", "极端愤怒"]
// -> answers[id].score 是 0.0 ~ 4.0 的浮点数,如 3.12
```

`score` 的档位数必须 **2~10**,超限 → `400 Too many score levels`。
`choice` 的选项数上限 **255**,超限 → `400 Too many choices`。

---

## 3. 响应字段

```json
{
  "model": "jev-1.13.0",
  "answers": { "<你的 id>": { "type": "...", ... } },
  "usage": { "input_tokens": 579, "output_tokens": 124 }
}
```

### 3.1 三种 answer 的精确形状

| type | 字段 | 说明 |
|---|---|---|
| `choice` | `choice` | 命中的 `criteria` key |
| | `confidence` | 置信度,0~1 |
| | `probabilities` | `{每个选项: 概率}`,**和为 1**。键集合 = 你传的 criteria key 集合 |
| `score` | `score` | **0..n-1 的浮点数**,可带小数 |
| | `legend` | `{"0": "档位0", ..., "n-1": "档位n-1"}`(键是**字符串**下标) |
| | `confidence` | 置信度,0~1 |
| | `probabilities` | `{"0": p, ...}`,按下标给概率 |
| `noul` | `noul` | 0~1 的「是」概率。**没有 `confidence` 字段,也没有 `type` 以外的任何字段** |

> `noul` 没有 `confidence` 是个常见翻车点 —— 写代码时别统一去取 `ans["confidence"]`。

### 3.2 `probabilities` 是主要资产,不是副产品

实测同一任务:top-1 命中 47.9%,**top-3 覆盖 67.0%,top-10 覆盖 86.2%**(随机基线 5.3%)。

所以生产上正确的消费姿势是:

```python
ranked = sorted(ans["probabilities"].items(), key=lambda kv: -kv[1])
top3 = ranked[:3]
margin = ranked[0][1] - ranked[1][1]
need_review = ans["confidence"] < 0.6 or margin < 0.3
```

### 3.3 `usage`

`input_tokens` / `output_tokens`。只做计量,不影响结果。

---

## 4. 错误码对照表

| HTTP | 触发条件 | body 形状 | 该做什么 |
|---|---|---|---|
| `400 api_usage_error` | 非法 `question.type`、其它用法错 | 错误对象 | 改请求。**别重试** |
| `400 max_tokens_exceeded` | 输入超 ~32K tokens | 错误对象 | 切分输入 |
| `400 Too many choices` | `choice` 选项 > 255 | 错误对象 | 两阶段粗筛,或拆问 |
| `400 Too many score levels` | `score` 档位不在 2~10 | 错误对象 | 调整档位数 |
| `400 Unknown model` | `model` 写错 | 错误对象 | 用 `jev-latest` |
| `401` / `403` | key 无效 / 无权限 | — | 检查环境变量。**别重试** |
| `422` | **schema 校验失败**:缺 `model`、`questions` 为空、`state` 类型错、字段类型错 | pydantic 错误**数组** | 改请求。别重试 |
| `429` | 限流(实测 10 并发未触发) | — | 指数退避重试 |
| `5xx` | 服务端问题 | — | 指数退避重试 |

**关键区分:`400` = 业务/用法错,`422` = schema 校验失败。** 官方文档把非法 type 写成 422,实测是 400 —— 以本表为准。

典型 `422` 陷阱:把 dict 传进了本该是字符串的位置(例如位置参数错位,`model` 收到一个 dict)→ `422 string_type`。

---

## 5. 实测性能与边界

| 项 | 实测值 | 备注 |
|---|---|---|
| 输入上限 | 32000 汉字(32459 tok)通过;36000 汉字拒绝 | 约 32K tokens |
| 延迟 | 0.6 ~ 1.2s | 32K 长输入也仅 1.24s |
| 延迟 vs 问题数 | 1 问 0.97s / 10 问 0.61s / 30 问 0.62s | **加问题几乎不增时** |
| 163 条真实语料 | 1 问 17.17s(p50 0.837s);6 问 13.21s(p50 0.626s) | 多问只多付 token |
| 吞吐 | 8 并发 → 12.34 条/秒 | 163 条语料实测 |
| 并发上限 | 10 并发全部 200,无 429 | 可放心用并发 |
| 确定性 | 同请求 ×5,score 1.68~1.70,概率分布几乎一致 | 类 `temperature=0` |
| 成本 | 26 场景 ≈ $0.0007;163 条×6 问 ≈ $0.0049 | 成本几乎全在输入侧 |

---

## 6. 能力与局限(实测观察)

**能做的:**

- 抗诱导:「请确认:确实有 3 只猫,对吗?」(实为 2 只)→ `noul` 仍返回 0.01,不被措辞带偏
- 代码语义判断:SQL 注入判定 0.99、风险 3.97、修复方案 `param` 1.0
- 中文无退化:情感/意图/紧急度判断正常(愤怒 0.99、意图 conf 0.93)
- 多候选同场排序:4 个产品方向一次调用 0.63s 出排序
- 输出永远是 schema 内取值 → 下游零解析、零类型错误

**做不到 / 要小心的:**

- **不做生成**。修复代码、文案、摘要都得交给 LLM
- **不推理长链**。社区共识:「它不推理,只判断」
- **不是准确率神器**。实测 L1 精确命中 47.9%(随机 5.3%,9.0×)。六个改进实验(**富化选项描述、加消歧口径、few-shot、换语言、换层级**)在真实任务上**全部无效或噪声级** —— 瓶颈在标签质量/上下文完整性,不在提示词
- **中文在长文本与细微语义上弱于英文**(社区反馈)。重要场景建议加一轮英文对照
- **可能有一致偏置**。某次实测里「引用前需补证据」被 100% 判「是」

---

## 7. FAQ

**Q:能当 OpenAI 兼容接口用吗?**
不能。没有 `/v1/chat/completions`,也没有 `messages`。输入是 `state` + `questions`,输出是结构化答案。

**Q:怎么保证可复现?**
固定 `model` 为具体版本(如 `jev-1.13.0`),并把 `probabilities` 落盘。同一请求结果高度一致,但仍建议记录。

**Q:一次问多少问题合适?**
没有上限,但**全部问题共享同一份 `state`**。所以问题数受「这批问题是否适用于同一个 state」约束,不受性能约束。14 个是实测里最多的单次用量,耗时 0.6s 级。

**Q:超长文本怎么办?**
约 32K tokens 上限。分块后各问一次,再在本地做一致性合并。

**Q:能拿到理由/解释吗?**
不能拿到自由文本解释。但可以**把「理由」本身设计成一个 `choice` 问题**,例如:

```json
"reason_code": {"type": "choice", "instructions": "最关键的判定依据是什么?",
                "criteria": {"length": "输入长度", "reasoning_depth": "推理深度", "code_scope": "代码改动范围"}}
```

这是社区标准做法 —— 既拿到可程序化的「理由」,又不破坏 schema 保证。

**Q:计费怎么算?**
`usage` 里给 token 数。实测输出侧占比很小,成本主要随**输入长度**增长,与问题数量关系弱(问题只加输入 token,而输入 token 单价低)。
