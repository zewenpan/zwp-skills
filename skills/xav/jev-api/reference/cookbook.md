# 生产用法手册(可抄的 question schema)

> 全部 26 例的**原始请求体与原始响应体**在 `../examples/real_io.json`(87KB)里,用 `id` 字段索引。
> 抄的时候不用手写 —— 直接 `json.load` 取出 `io.request`,`state` 换成你的数据就能跑。

---

## 0. 怎么选 type(先想清楚这一步,后面都是体力活)

| 你要的判断是… | 用 | 返回 |
|---|---|---|
| 从有限集合里选一个(类别、路由、动作) | `choice` | 命中的 key + 全量概率 |
| 有序程度、强度、优先级、匹配度 | `score` | 0..n-1 浮点分 + 档位名 |
| 是/否、要不要、该不该 | `noul` | 0~1 概率 |

**口诀:能二分就用 `noul`,能排序就用 `score`,`choice` 留给真正的分类。**

`choice` 的一个隐藏优势:它的 `probabilities` 天然就是「候选排序」,所以高基数场景(>10 类)首选做法是 **`score` 粗筛 → `choice` 精选**(见 §3)。

---

## 1. 路由与分诊

### 1.1 LLM 模型路由 —— 决定这条请求值不值得喂给 frontier

出处:`examples/real_io.json` → `A1`

```json
{
  "route": {"type": "choice", "instructions": "这条请求应该路由给哪一档模型?判断依据是任务的认知负荷。",
    "criteria": {"tiny": "微型模型:改写/格式化/翻译等确定性改写",
                 "small": "小模型:单文件代码改动、简单问答",
                 "mid": "中档模型:多文件重构、需要一定推理",
                 "frontier": "前沿模型:需要长链推理、架构设计、开放研究"}},
  "reason_code": {"type": "choice", "instructions": "最关键的判定依据是什么?",
    "criteria": {"length": "输入长度", "reasoning_depth": "推理深度",
                 "code_scope": "代码改动范围", "ambiguity": "需求歧义度"}},
  "confident": {"type": "noul", "instructions": "是否确信该路由判断,无需人工介入?"}
}
```

要点:输出直接是代码里的 `switch` 分支。加 `reason_code` 是为了**拿到可程序化的「理由」而不破坏 schema** —— 这是社区标准手法。

### 1.2 四路分流 —— Agent 平台的骨架决策

出处:`A3`。`agent` / `human` / `replan` / `block`,配一个 `score` 量后果严重度 + 一个 `noul` 判是否需要法务审批。

### 1.3 客服入口:意图 + 情绪 + 缺槽,一次出

出处:`A4`

```json
{
  "intent": {"type": "choice", "instructions": "核心意图?",
    "criteria": {"refund": "要求退款", "explain": "要求解释扣费原因",
                 "cancel": "要求确认/完成取消", "complain": "单纯发泄投诉"}},
  "emotion": {"type": "score", "instructions": "负面情绪强度",
    "criteria": ["平静", "轻微不悦", "明显不满", "愤怒", "极端愤怒"]},
  "need_clarify": {"type": "noul", "instructions": "是否缺少必要信息,需要先向客户追问?"},
  "missing_slot": {"type": "choice", "instructions": "最关键的缺失信息是什么?",
    "criteria": {"order_id": "订单/账号 ID", "date": "扣费时间",
                 "channel": "扣费渠道", "none": "信息已足够"}}
}
```

### 1.4 生产告警分诊:决定叫不叫人起床

出处:`B2`。四个动作 `page` / `ticket` / `silence` / `watch`,配 `severity`(score)+ `rollback`(noul)。告警风暴里最贵的是人的注意力。

### 1.5 工单分诊(替代「训分类器 + 一堆正则」)

出处:`B1`。`category` + `urgency(P0~P3)` + `escalate(noul)` + `churn_risk(noul)`。**零训练上场**。

---

## 2. 门控与审核(Agent 安全最实在的一层)

### 2.1 工具调用准入 —— 每次 tool call 前问一次

出处:`C1`

```json
{
  "verdict": {"type": "choice", "instructions": "是否允许执行该工具调用?",
    "criteria": {"allow": "允许,直接执行", "confirm": "需人工二次确认后执行",
                 "deny": "拒绝执行", "sandbox": "降级到沙箱/只读环境执行"}},
  "blast_radius": {"type": "score", "instructions": "若执行出错的影响面",
    "criteria": ["无", "单实例", "单服务", "多服务", "全站"]},
  "is_prod": {"type": "noul", "instructions": "该操作是否触碰生产环境?"}
}
```

`state` 里要带上:命令内容、执行身份、目标环境、有无人工值班、近期故障记录。**信息不全时判断必然失真 —— 这不是模型的锅。**

### 2.2 UGC 多维合规 —— 四维一次出

出处:`D3`。`harassment` / `threat` / `spam`(三个 noul)+ `action`(choice)+ `severity`(score)。

**这是「问题并行不增时」最直接的省钱手法**:四个独立维度拆四次调用要 4× 往返,塞一次只要 1×。

### 2.3 Shadow gate —— 先只观察不拦

出处:`D2`。把一批历史内容跑一遍,先**看分布**再决定要不要上闸门。判定文本是否在断言因果 / 预测 / 建议,配合 `temporal_claim` / `needs_citation` 两个 noul。

**先只建议不执行,观察一段时间再放权** —— 这是所有 gate 类应用的生产上线姿势。

### 2.4 审核的姿势:概率 + 动作两档都要

出处:`D1`。审核类最讲究「宁放勿错杀」,所以 `spam`(noul 概率)和 `action`(choice 动作)必须同时拿:概率用来调阈值,动作用来驱动流程。

---

## 3. 高基数:两阶段 Score → Choice

出处:`H3`

```
第一阶段  score 粗筛
  {"domain": {"type":"score", "instructions":"该请求属于哪个一级域?",
              "criteria":["售前咨询","售后维修/退换","账单支付","账号权限","物流配送","投诉建议"]}}
        ↓ 在本地取 score 附近的 2~3 个域
第二阶段  choice 精选
  {"sub": {"type":"choice", "instructions":"在「售后维修/退换」内部,具体属于哪一类?",
           "criteria":{...5 个选项...}}}
```

实测合计 1.802s(0.983 + 0.819)。两阶段用一个常量代价先把范围收窄,比一次 50 选 1 稳得多。

---

## 4. 批量打标(最省钱的形态)

### 4.1 一条内容,14 个是/否

出处:`E1`。**14 个问题塞进一次调用,只付一次往返。** 实测 163 条 × 6 问:1 问 17.17s(p50 0.837s)vs 6 问 13.21s(p50 0.626s) —— 问题数对延迟几乎无影响,多付的只是输入 token。

### 4.2 文献初筛:纳入 / 排除 / 待定 + 排除理由码

出处:`E3`

```json
{
  "decision": {"type": "choice", "instructions": "该题录是否应进入全文筛选?",
    "criteria": {"include": "纳入全文", "exclude": "排除", "unsure": "待定"}},
  "exclude_reason": {"type": "choice", "instructions": "若排除,主要理由是什么?",
    "criteria": {"pop": "人群不符", "design": "研究设计不符", "outcome": "结局指标不符",
                 "lang": "语言不符", "dup": "重复发表", "na": "不适用"}},
  "is_rct": {"type": "noul", "instructions": "是否为随机对照试验?"},
  "confidence_ok": {"type": "noul", "instructions": "该判断是否足以支撑直接排除(无需人工复核)?"}
}
```

**把「机器可自动排除的」和「必须人看的」分开** —— `confidence_ok` 就是那个分流阀。

---

## 5. 上下文与记忆管理(Agent 长程任务的命门)

### 5.1 工具调用结果处置:keep / compress / discard

出处:`F1`。把上下文管理从「阈值硬截断」变成语义判断。配 `keep_what`(choice:保留哪段)、`context_pressure`(score)、`safe_to_drop`(noul)。

### 5.2 记忆写入决策

出处:`F2`。`write_memory`(noul)+ `memory_type`(choice)+ `ttl`(choice)+ `should_schedule`(noul)。

记忆库被垃圾污染是 Agent 的慢性病;让 Jev 当守门人比按关键词/长度过滤靠谱得多。

---

## 6. 浏览器 / Computer Use 的单步动作

出处:`G1`、`G2`。

```json
{
  "action": {"type": "choice", "instructions": "下一步应该执行哪个动作?",
    "criteria": {"click": "点击某个元素", "type": "输入文本",
                 "scroll": "滚动", "back": "返回上一页",
                 "extract": "提取信息", "done": "任务完成"}},
  "target": {"type": "choice", "instructions": "动作作用在哪个元素上?",
    "criteria": {"<元素id或语义描述>": "..."}},
  "confidence_ok": {"type": "noul", "instructions": "该动作是否足够确定,可直接执行?"}
}
```

**核心洞见:点击 = 从 DOM 里做分类,不是长文生成。** 把结构化 DOM 观察(标签 + 文本 + 可点性)塞进 `state`,拿回一个动作。

---

## 7. 打分与裁判

### 7.1 线索打分:不训分类器也能排序

出处:`H1`。`icp_fit` + `intent`(两个 score)+ `priority` + `blocker`(两个 choice)。**冷启动场景最实用:没有标注数据也能上线。**

### 7.2 让 Jev 当裁判

出处:`H2`。三个 `noul` 分别判三个必过条件(pass_a/b/c)+ `verdict`(choice)+ `score`(质量分)+ `weakest`(choice:最弱环节)。

**把「人工 review」变成「Jev 判 + 只看它标的高风险项」**,是评测与内容质检里最省钱的一招。

### 7.3 完成度验证:Agent 自称完成,证据是否成立

出处:`I4`。`verified`(noul)+ `claim_honest`(choice)+ `next_action`(choice)+ `trust_delta`(score)。

**Agent 撒谎的方式不是编造文本,而是过早宣布胜利。** 这一问价廉物美。

---

## 8. 多候选同场排序(state 用对象 / 数组)

出处:`I3`。`state` 是一个 object,`instructions` 里用反引号引用键:

```json
{
  "state": {"polyu_ime": "...", "hku_idt": "...", "hkust_amc": "..."},
  "questions": {
    "polyu_ime": {"type": "score", "instructions": "`polyu_ime` 与候选人背景的匹配度?",
                  "criteria": ["不匹配","偏弱","一般","较好","高度匹配"]},
    "best_fit": {"type": "choice", "instructions": "综合来看最适合哪个?",
                 "criteria": {"polyu_ime": "...", "hku_idt": "...", "hkust_amc": "..."}}
  }
}
```

**把「GPA 换算 × 课程匹配 × 作品集 × 职业目标」这类多维判断一次性摊平,比逐个写长 prompt 更稳。**

---

## 9. 全 26 例索引

| id | 组 | 场景 | 一次问几个 | state |
|---|---|---|---|---|
| A1 | 路由 | LLM 模型档位路由 | 3 | str |
| A2 | 路由 | Agent 下一步 proceed/cheaper_first/skip | 2 | str |
| A3 | 路由 | 四路分流 agent/human/replan/block | 3 | str |
| A4 | 路由 | 意图 + 情绪 + 缺槽 | 4 | str |
| B1 | 分诊 | 客服工单(类别+紧急度+转人工+流失风险) | 4 | str |
| B2 | 分诊 | 告警:真故障 vs 噪声 | 3 | str |
| C1 | 门控 | 工具调用准入 | 3 | str |
| C2 | 门控 | 代码注入风险 + 修复方案 | 4 | str |
| C3 | 门控 | 交易风控实时判决 | 4 | str |
| D1 | 审核 | Discord 诈骗链接 | 4 | str |
| D2 | 审核 | Shadow gate(因果/预测/建议) | 3 | str |
| D3 | 审核 | UGC 四维合规 | 5 | str |
| E1 | 批量 | 一条内容 14 个是/否打标 | 14 | str |
| E2 | 批量 | NHTSA 投诉 6 分类 | 4 | str |
| E3 | 批量 | 系统评价文献初筛 | 4 | str |
| F1 | 压缩 | 工具结果 keep/compress/discard | 4 | str |
| F2 | 压缩 | 记忆写入决策 | 4 | str |
| G1 | 浏览器 | 单步动作选择 | 3 | str |
| G2 | 电脑操作 | 界面语义定位可点目标 | 3 | str |
| H1 | 打分 | 线索打分排序 | 4 | str |
| H2 | 打分 | 当裁判:输出是否达标 | 6 | str |
| H3 | 打分 | 高基数两阶段(score→choice) | 1+1 | str |
| I1 | 陪伴 | 此刻该不该主动开口 | 4 | str |
| I2 | 语音 | 这段输入是不是自己的 TTS 回声 | 4 | str |
| I3 | 排序 | 6 个项目匹配打分 | 6 | str |
| I4 | 验证 | Agent 自称完成,证据是否成立 | 4 | str |

> 26 例合计 17.54s,平均延迟 0.67s,全部 HTTP 200,总输入 ~16k tokens ≈ $0.0007。

---

## 10. 抄之前先看这三条

1. **提示词工程常常无效。** 实测六个改进实验(富化选项描述 / 加消歧口径 / few-shot / 换语言 / 换层级 / 50选1映射回19选1)**全部无效或噪声级**。低准确率时最该做的是去看错误样本,不是改 prompt。
2. **`criteria` 的说明写「边界」而不是「同义词」。** `{"refund": "退款"}` 不如 `{"refund": "明确要求退钱;若只是问为什么扣费应选 explain"}`。但注意:这份收益有限,别指望靠它解决分类体系本身的模糊。
3. **输出候选 + 复核标记,别输出唯一答案。** `confidence < 0.6` 或 `top1-top2 概率差 < 0.3` 或两策略分歧 → 标复核。
