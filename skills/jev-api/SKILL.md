---
name: jev-api
description: TypeSafe Jev(System One,社区口头叫 "jav")的最小可用 API 手册与零依赖客户端——只填一个环境变量 TYPESAFE_API_KEY 就能直接调用,不需要读官方文档。当任务需要给文本/对象做结构化判定:分类、打标、路由、多档打分、是/否门控、分诊、审核、置信度分流,或需要在 LLM 之外加一个 0.6s 级的确定性「决策层」时使用。关键词:jev、jav、typesafe、system one、systemone、noul、choice、score、结构化分类、打标、路由、triage、guardrail、置信度门控、决策模型。
agent_created: true
---

# TypeSafe Jev(System One)——最小 API 手册

**一句话定位:这不是聊天模型,是决策模型。** 给它一个 `state` 加一组**类型化问题**,它直接返回**代码可消费的结构化答案** —— 没有文本生成、没有解析环节、不会返回选项外的值。

> 社区/用户口语常把它叫 **"jav"**,指的是同一个东西。

## 0. 30 秒上手(只需要一个环境变量)

> 下面所有 `scripts/…` 路径都相对**本 skill 目录**。命令里的 `python` 指 Python 3.8+,客户端只用标准库。

```bash
# 1) 填 key(唯一必填项)
export TYPESAFE_API_KEY=apikey_xxx        # Windows: setx TYPESAFE_API_KEY apikey_xxx

# 2) 自检:验证连通性、三类原语、契约形状(会真发一次调用,几厘钱)
python scripts/jev.py --selftest

# 3) 直接问
python scripts/jev.py --state "我的订单三天没发货,客服也不回" \
                      --ask "核心诉求?" --choices refund=要求退款,ship=催发货,complain=投诉
```

看到 `自检结果: PASS` 就说明可以用了。**本 skill 自带客户端和离线测试,不需要再查任何文档、不需要联网搜用法。**

## 1. 契约(全部就这些)

```
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer $TYPESAFE_API_KEY
Content-Type: application/json
```

请求体三个字段,**没有第四个**:

```json
{
  "state": "待判断的文本 / 对象 / 数组",
  "model": "jev-latest",
  "questions": {
    "<你的问题id>": { "type": "choice", "instructions": "...", "criteria": {...} }
  }
}
```

| 字段 | 说明 |
|---|---|
| `state` | `string` / `object` / `array` 都行。是对象/数组时,在 `instructions` 里用**反引号** `` `key` `` 引用其中的键(实测可用) |
| `model` | `jev-latest`(滚动)或固定版本如 `jev-1.13.0`。写错直接 `400 Unknown model`,不会静默降级 |
| `questions` | 键是**你自己起的 id**,会原样出现在响应的 `answers` 里。多个问题同场评估 |
| `instructions` | 自然语言问法。可以内嵌结构化数据(dict/list),用反引号引用 |
| `criteria` | `choice` 用 **dict**(key 就是返回值);`score` 用 **list**(返回下标);`noul` 不写 |

响应体也是三个字段:

```json
{
  "model": "jev-1.13.0",
  "answers": { "intent": { "type": "choice", "choice": "refund", "confidence": 0.99,
                           "probabilities": {"refund": 1.0, "explain": 0.0} } },
  "usage": { "input_tokens": 579, "output_tokens": 124 }
}
```

## 2. 三种原语(可任意混用)

| type | 请求里写什么 | 响应的 `answers[id]` |
|---|---|---|
| `choice` | `criteria` = `{"选项key": "给模型看的说明"}` | `{type, choice, confidence, probabilities{选项:概率}}` |
| `score` | `criteria` = `["档位0","档位1",...,"档位n-1"]`(2~10 档) | `{type, score, confidence, legend{"0":"档位0",...}, probabilities{"0":p,...}}` |
| `noul` | 只需要 `instructions` | `{type, noul}` ← **0~1 的概率,注意没有 `confidence` 字段** |

`score` 的 `score` 是 **0..n-1 的浮点数**(可以带小数,如 `3.12`),不是整数。取档位名用 `legend[str(round(score))]`,`scripts/jev.py` 里的 `score_label()` 已经封装好。

## 3. 最小可运行代码

**Python(零依赖,直接用本 skill 的客户端):**

```python
import sys; sys.path.insert(0, "<skill>/scripts")
from jev import ask_choice, ask_noul, ask_score, call

r = ask_choice("订单三天没发货", "核心诉求?", {"refund": "退款", "ship": "催发货"})
print(r["choice"], r["confidence"], r["probabilities"])

# 多个问题一次问完(强烈推荐,见 §5.1)
body = call("订单三天没发货,客服也不回", {
    "intent":  {"type": "choice", "instructions": "核心诉求?", "criteria": {"refund": "退款", "ship": "催发货"}},
    "urgency": {"type": "score",  "instructions": "紧急度", "criteria": ["很低","低","中","高","很高"]},
    "human":   {"type": "noul",   "instructions": "是否必须转人工?"},
})
print(body["answers"]["urgency"]["score"], body["usage"])
```

**curl(不依赖任何脚本):**

```bash
curl -s https://api.typesafe.ai/v1/systemone \
  -H "Authorization: Bearer $TYPESAFE_API_KEY" -H "Content-Type: application/json" \
  -d '{"state":"订单三天没发货","model":"jev-latest",
       "questions":{"q":{"type":"noul","instructions":"用户是否明显不满?"}}}'
```

**Node(18+,自带 fetch):**

```js
const r = await fetch("https://api.typesafe.ai/v1/systemone", {
  method: "POST",
  headers: { Authorization: `Bearer ${process.env.TYPESAFE_API_KEY}`, "Content-Type": "application/json" },
  body: JSON.stringify({ state, model: "jev-latest", questions }),
});
const { answers } = await r.json();
```

**批量(8 并发实测 12.34 条/秒):**

```bash
python scripts/jev.py --jsonl rows.jsonl -j 8 --out out.jsonl
# rows.jsonl 每行: {"state": "...", "questions": {...}}
```

## 4. 硬边界(实测值,不是文档抄的)

| 项 | 值 |
|---|---|
| 输入上限 | **约 32K tokens**(32000 汉字通过,36000 报 `400 max_tokens_exceeded`) |
| 单次延迟 | **0.6~1.2s**,主要由**输入长度**决定,与问题数量几乎无关 |
| 加问题的代价 | 1 问 0.837s vs 6 问 0.626s —— **加问题几乎不加时**,只加输入 token |
| `choice` 选项上限 | **255**(超限 `400 Too many choices`) |
| `score` 档位数 | **2~10**(超限 `400 Too many score levels`) |
| 并发 | 10 并发无 429,可放心用线程池/协程 |
| 确定性 | 高。同请求重复调用结果几乎一致(类 `temperature=0`),生产可放心做幂等重试 |
| 成本量级 | 实测 26 个生产场景合计 ≈ **$0.0007**;163 条 × 6 问 ≈ **$0.0049** |

## 5. 踩坑(文档与现实的差异)

| 现象 | 实际行为 |
|---|---|
| 非法 `question.type` | 官方文档说 422,**实际是 `400 api_usage_error`** |
| `422` 什么时候出现 | **只用于 schema 校验失败**:缺 `model`、`questions` 为空、`state` 类型错、字段类型错(如把 dict 塞进字符串位置)。body 是 pydantic 错误数组 |
| 模型名写错 | `400 Unknown model`,不会静默降级 |
| 想要 chat 接口 | **没有** `/v1/chat/completions`(404)。它不做文本生成,别当通用 LLM 用 |
| 列模型 | `GET /v1/models` 可用,当前只有 `jev-latest` / `jev-preview`(都解析到 `jev-1.13.0`) |
| 超长输入 | 报 `400 max_tokens_exceeded`,需要自己先切分 |

## 6. 六个必须知道的用法要点

1. **永远把问题塞进同一次调用。** 问题之间独立并行评估,所以「先定大类 + 每个大类内部各自细判 + 直接全量选一次做交叉验证」三种策略可以一个价拿到。串行一问一答是纯浪费。
2. **一定要存下 `probabilities`。** 只取 `argmax` 会扔掉大部分信息 —— 实测 top-1 命中 47.9%,而 **top-3 覆盖 67.0%、top-10 覆盖 86.2%**。生产上输出「候选 + 复核标记」比输出唯一答案可靠得多。
3. **置信度是分界线,不是准确率指标。** 诊断型判断置信度很高(0.97~1.00),开放型判断普遍偏低(0.20~0.62)。**低置信 ≠ 判错,而是「这个问题本身不可分」** —— 用它决定「要不要升级给人工/要不要追问」,别拿它当准确率。
4. **别预设置信度是校准的。** 在真实且标签模糊的任务上它**过度自信**:`confidence ≥ 0.99` 的样本只对了 61.7%;判对均值 0.897 vs 判错 0.808,只差 0.089。人造的「明确/模糊」对照里它表现完美,但那是任务本身可分带来的,不能外推。
5. **高基数用两阶段:先 `score` 粗筛,再 `choice` 精选。** `choice` 上限是 255,但真痛点是「一次选一个」在高基数下不可靠。两阶段用一个常量代价先缩小范围。
6. **「零幻觉」只指 schema 保证。** 它不会返回选项外的值、不会有类型错误 —— 但**不等于判断总是对的**。可以出现一致偏置(某次实测里「引用前需补证据」被 100% 判「是」)。

**反模式(别这么干):** 把它当聊天模型用 / 串行地一问一答 / 只取 top-1 丢掉概率分布 / 拿低置信度当「模型不行」的证据 / 直接采信置信度做业务阈值而不先在自己的数据上验证。

## 7. 文件导航

| 路径 | 什么时候读 |
|---|---|
| `scripts/jev.py` | 唯一的客户端。零依赖(Python 3.8+),既是库也是 CLI。**先跑 `--selftest`** |
| `tests/test_jev.py` | 离线回归测试(不需要 key、不需要联网):重放 27 个真实历史请求/响应 + mock server 压 HTTP 链路。改代码后跑它 |
| `reference/contract.md` | 想深挖字段语义、错误码、计费口径、历史版本差异 |
| `reference/cookbook.md` | 想抄生产场景的 question schema(路由/分诊/门控/审核/批量/压缩/评分/裁判等 20+ 例) |
| `examples/real_io.json` | 26 组**真实调用的原始请求/响应**(87KB)。照着改最省事,且可被 `tests/` 重放校验 |

## 8. 环境变量与代理

- 认 `TYPESAFE_API_KEY`,备用 `JEV_API_KEY`;CLI 也支持 `--key`(不建议,会进 shell 历史)。
- 国内可直连 `api.typesafe.ai`,**通常不需要代理**。需要走代理时设置 `HTTPS_PROXY`(urllib / fetch 都会自动读取)。
