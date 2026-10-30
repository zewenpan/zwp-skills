#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jev.py — TypeSafe Jev / System One(社区口头叫 "jav") 的最小零依赖客户端 + 命令行。

设计目标:只填一个环境变量就能用,不需要读任何文档。

    Windows  :  setx TYPESAFE_API_KEY apikey_xxx      (新开终端生效)
    mac/Linux:  export TYPESAFE_API_KEY=apikey_xxx

先自检(会真的发一次调用,几厘钱):

    python jev.py --selftest

当库用:

    from jev import ask_choice, ask_score, ask_noul, call

    r = ask_choice("我的订单三天没发货,客服也不回", "核心诉求?",
                   {"refund": "要求退款", "ship": "催发货", "complain": "投诉服务"})
    print(r["choice"], r["confidence"])          # -> ship 0.97

命令行用:

    python jev.py --state "我的订单三天没发货" --ask "核心诉求?" --choices refund=退款,ship=催发货
    python jev.py --state-file s.txt --ask "紧急度?" --score "很低,低,中,高,很高"
    python jev.py --state "..." --ask "需要转人工吗?" --noul
    python jev.py --json payload.json            # 完整自定义请求体
    python jev.py --jsonl rows.jsonl -j 8        # 批量:每行 {"state":..., "questions":{...}}
    python jev.py --dry-run --state "..." --ask "..." --choices a=A,b=B    # 只看请求体

只依赖标准库(Python 3.8+)。走代理时设置 HTTPS_PROXY 即可,urllib 会自动读取。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

__all__ = [
    "BASE_URL", "SYSTEMONE_URL", "MODELS_URL", "DEFAULT_MODEL", "ENV_VARS",
    "JevError", "JevAuthError", "JevHTTPError",
    "api_key", "build_payload", "call", "call_meta", "ask",
    "ask_choice", "ask_score", "ask_noul", "batch", "list_models", "score_label",
]

BASE_URL = "https://api.typesafe.ai"
SYSTEMONE_URL = BASE_URL + "/v1/systemone"
MODELS_URL = BASE_URL + "/v1/models"
DEFAULT_MODEL = "jev-latest"
ENV_VARS = ("TYPESAFE_API_KEY", "JEV_API_KEY")

_LIB_HINT = "缺少 API key:请设置环境变量 TYPESAFE_API_KEY(或 JEV_API_KEY)"


# --------------------------------------------------------------------------- 异常
class JevError(Exception):
    """jev 客户端的基类异常。"""


class JevAuthError(JevError):
    """未配置 key,或服务端返回 401 / 403。"""


class JevHTTPError(JevError):
    """服务端返回非 2xx。区分「用法错(400/422)」与「服务端错(5xx)」。"""

    def __init__(self, status, body, url=SYSTEMONE_URL):
        self.status = status
        self.body = body
        self.url = url
        super().__init__(self._explain())

    def _explain(self):
        detail = self.body if isinstance(self.body, str) else json.dumps(self.body, ensure_ascii=False)
        detail = (detail or "").strip()[:600]
        hint = {
            400: "用法/业务错(如非法 question type、模型名错、超限)",
            401: "key 无效或缺失",
            403: "key 无权访问该资源",
            422: "schema 校验失败(缺 model / 空 questions / state 类型错 / 字段类型错)",
            429: "限流,退避重试",
        }.get(self.status, "")
        return "HTTP %s %s | %s" % (self.status, hint, detail)


# ------------------------------------------------------------------------- 环境 / key
def api_key(explicit=None):
    """按 显式入参 -> TYPESAFE_API_KEY -> JEV_API_KEY 的顺序取 key。"""
    if explicit:
        return explicit
    for name in ENV_VARS:
        val = os.environ.get(name)
        if val and val.strip():
            return val.strip()
    raise JevAuthError(_LIB_HINT)


# --------------------------------------------------------------------------- 传输
def _post(url, payload, key, timeout, retries):
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    last = None
    for attempt in range(max(1, retries)):
        req = urllib.request.Request(url, data=raw, method="POST")
        req.add_header("Authorization", "Bearer " + key)
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8")), time.perf_counter() - t0
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            if exc.code in (401, 403):
                raise JevAuthError("HTTP %s | %s" % (exc.code, body[:300])) from None
            # 5xx / 429 值得重试;4xx 是确定性错误,重试没意义
            if exc.code in (429, 500, 502, 503, 504, 529) and attempt < retries - 1:
                last = JevHTTPError(exc.code, body, url)
                time.sleep(2 ** attempt)
                continue
            raise JevHTTPError(exc.code, body, url) from None
        except urllib.error.URLError as exc:
            if attempt < retries - 1:
                last = exc
                time.sleep(2 ** attempt)
                continue
            raise JevError("网络错误: %s" % exc) from None
    raise last if last else JevError("请求失败")


# --------------------------------------------------------------------------- 请求体
def build_payload(state, questions, model=DEFAULT_MODEL):
    """构造请求体。state 可为 str / dict / list;questions 为 {id: question}。

    这是本地唯一构造请求体的地方 —— 保证脚本、CLI、测试三者零漂移。
    """
    if not isinstance(questions, dict) or not questions:
        raise JevError("questions 必须是非空 dict")
    for qid, q in questions.items():
        if not isinstance(q, dict) or "type" not in q:
            raise JevError("question %r 必须是含 type 的 dict" % qid)
        if q["type"] not in ("choice", "score", "noul"):
            raise JevError("question %r 的 type=%r 非法,只支持 choice / score / noul"
                           % (qid, q["type"]))
    return {"state": state, "model": model, "questions": questions}


def call(state, questions, model=DEFAULT_MODEL, key=None, timeout=60, retries=3):
    """发一次请求,返回服务端原始响应体 {model, answers, usage}。"""
    body, _ = call_meta(state, questions, model=model, key=key, timeout=timeout, retries=retries)
    return body


def call_meta(state, questions, model=DEFAULT_MODEL, key=None, timeout=60, retries=3):
    """同 call(),额外返回 (body, 耗时秒)。"""
    payload = build_payload(state, questions, model)
    body, elapsed = _post(SYSTEMONE_URL, payload, api_key(key), timeout, retries)
    if not isinstance(body, dict) or "answers" not in body:
        raise JevError("响应不是预期的 {model, answers, usage}: %s"
                       % json.dumps(body, ensure_ascii=False)[:300])
    return body, elapsed


def list_models(key=None, timeout=30):
    """GET /v1/models。当前只有 jev-latest / jev-preview,都解析到 jev-1.13.0。"""
    req = urllib.request.Request(MODELS_URL, method="GET")
    req.add_header("Authorization", "Bearer " + api_key(key))
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ------------------------------------------------------------------------ 单问题糖
def ask(state, question, model=DEFAULT_MODEL, question_id="q", **kw):
    """问单个问题,只返回该问题的答案对象(不含 usage)。"""
    if isinstance(question, dict):
        spec = dict(question)
    else:
        spec = {"type": "choice", "instructions": str(question), "criteria": kw.pop("criteria")}
    spec.setdefault("type", "choice")
    body = call(state, {question_id: spec}, model=model, **kw)
    return body["answers"][question_id]


def ask_choice(state, instructions, criteria, model=DEFAULT_MODEL, **kw):
    """criteria: {选项key: 说明}。返回 {type, choice, confidence, probabilities}。"""
    return ask(state, {"type": "choice", "instructions": instructions, "criteria": criteria},
               model=model, **kw)


def ask_score(state, instructions, criteria, model=DEFAULT_MODEL, **kw):
    """criteria: [档位1, 档位2, ...](2~10 档)。返回 {score(0..n-1 浮点), legend, confidence, probabilities}。"""
    if not isinstance(criteria, (list, tuple)) or not 2 <= len(criteria) <= 10:
        raise JevError("score 的 criteria 必须是 2~10 个有序档位(列表)")
    return ask(state, {"type": "score", "instructions": instructions, "criteria": list(criteria)},
               model=model, **kw)


def ask_noul(state, instructions, model=DEFAULT_MODEL, **kw):
    """是/否。返回 {type, noul}(0~1 概率,注意没有 confidence 字段)。"""
    return ask(state, {"type": "noul", "instructions": instructions}, model=model, **kw)


def score_label(answer):
    """把 score 的浮点分换算成可读档位名。score 是连续值,四舍五入到最近的档位。"""
    legend = answer.get("legend") or {}
    if not legend:
        return None
    idx = int(round(float(answer["score"])))
    idx = max(0, min(idx, max(int(k) for k in legend)))
    return legend.get(str(idx))


# --------------------------------------------------------------------------- 批量
def batch(states, questions, workers=8, model=DEFAULT_MODEL, key=None,
          timeout=60, retries=3, on_error="raise"):
    """并发地对多条 state 问同一组 questions。

    on_error="raise" 立刻抛;on_error="skip" 则该条返回 {"error": "..."}。
    返回 [(state, answers_or_error_dict), ...],顺序与入参一致。
    """
    def one(state):
        try:
            body = call(state, questions, model=model, key=key, timeout=timeout, retries=retries)
            return state, body["answers"]
        except JevError as exc:
            if on_error == "raise":
                raise
            return state, {"error": str(exc)}

    results = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for item in pool.map(one, states):
            results.append(item)
    return results


# ------------------------------------------------------------------------- 渲染
def render_answer(answer):
    """把单个 answer 渲染成人读文本(多行字符串)。"""
    kind = answer.get("type")
    lines = []
    if kind == "choice":
        lines.append("  choice = %s   confidence = %s" % (answer.get("choice"), answer.get("confidence")))
        probs = answer.get("probabilities") or {}
        for opt, p in sorted(probs.items(), key=lambda kv: -kv[1]):
            lines.append("    %5.3f  %s%s" % (p, opt, "   <=" if opt == answer.get("choice") else ""))
    elif kind == "score":
        lines.append("  score  = %.2f -> %s   confidence = %s"
                     % (answer.get("score", 0), score_label(answer), answer.get("confidence")))
        legend = answer.get("legend") or {}
        probs = answer.get("probabilities") or {}
        for idx, p in sorted(probs.items(), key=lambda kv: int(kv[0])):
            lines.append("    %5.3f  [%s] %s" % (p, idx, legend.get(str(idx), "")))
    elif kind == "noul":
        lines.append("  noul   = %.3f   (是/否概率;noul 无 confidence 字段)" % answer.get("noul", 0.0))
    else:
        lines.append("  " + json.dumps(answer, ensure_ascii=False))
    return "\n".join(lines)


def render_response(state, questions, body, elapsed=None):
    out = []
    head = state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)
    head = head.replace("\n", " ")
    out.append("state: " + (head[:110] + " ..." if len(head) > 110 else head))
    out.append("model: %s" % body.get("model"))
    out.append("")
    for qid, q in questions.items():
        ans = (body.get("answers") or {}).get(qid)
        out.append("Q[%s] %s" % (qid, q.get("instructions", "")))
        if ans is None:
            out.append("  (缺答案)")
        else:
            out.append(render_answer(ans))
        out.append("")
    usage = body.get("usage") or {}
    tail = "usage: in=%s out=%s" % (usage.get("input_tokens"), usage.get("output_tokens"))
    if elapsed is not None:
        tail += "   latency=%.3fs" % elapsed
    out.append(tail)
    return "\n".join(out)


# --------------------------------------------------------------------------- CLI
def _parse_choices(text):
    """'a=说明,b=说明' 或 'a,b' -> {key: description}。"""
    criteria = {}
    for chunk in text.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" in chunk:
            k, v = chunk.split("=", 1)
            criteria[k.strip()] = v.strip()
        else:
            criteria[chunk] = chunk
    if not criteria:
        raise JevError("--choices 解析后为空")
    return criteria


def _read_state(args):
    if args.state_json:
        return json.loads(args.state_json)
    if args.state_file:
        with open(args.state_file, encoding="utf-8") as fh:
            return fh.read()
    if args.state is None:
        raise JevError("缺少 state:用 --state / --state-file / --state-json")
    if args.state == "-":
        return sys.stdin.read()
    return args.state


def _single_question(args):
    """把 --ask + (--choices|--score|--noul) 组装成一个 question spec。"""
    if not args.ask:
        return None
    given = [bool(args.choices), bool(args.score), bool(args.noul)]
    if sum(given) > 1:
        raise JevError("--choices / --score / --noul 只能三选一")
    if args.choices:
        return {"type": "choice", "instructions": args.ask, "criteria": _parse_choices(args.choices)}
    if args.score:
        levels = [s.strip() for s in args.score.split(",") if s.strip()]
        return {"type": "score", "instructions": args.ask, "criteria": levels}
    if args.noul:
        return {"type": "noul", "instructions": args.ask}
    raise JevError("--ask 需要配合 --choices / --score / --noul 之一")


def _selftest(args):
    print("=" * 68)
    print("jev 自检 —— 1) 环境变量  2) 连通性  3) 三类原语  4) 契约形状")
    print("=" * 68)
    found = [n for n in ENV_VARS if os.environ.get(n, "").strip()]
    print("[1] 环境变量 %s : %s" % ("/".join(ENV_VARS), ("已设置 " + ", ".join(found)) if found else "未设置"))
    try:
        key = api_key(args.key)
    except JevAuthError as exc:
        print("    FAIL %s" % exc)
        print("    Windows: setx TYPESAFE_API_KEY apikey_xxx   (然后重开终端)")
        print("    mac/Linux: export TYPESAFE_API_KEY=apikey_xxx")
        return 2
    print("    key 前缀 %s...(已就绪)" % key[:10])

    try:
        models = list_models(key)
        print("[2] GET /v1/models -> %s" % json.dumps(models, ensure_ascii=False)[:200])
    except Exception as exc:  # noqa: BLE001
        print("[2] GET /v1/models 失败(不致命): %s" % exc)

    questions = {
        "intent": {"type": "choice", "instructions": "该消息的核心诉求是什么?",
                   "criteria": {"refund": "要求退款", "ship": "催发货",
                                "complain": "投诉服务态度", "other": "其他"}},
        "urgency": {"type": "score", "instructions": "紧急程度", "criteria": ["很低", "低", "中", "高", "很高"]},
        "need_human": {"type": "noul", "instructions": "是否必须转人工处理?"},
    }
    state = "用户消息:我的订单 #88213 三天了还没发货,客服也不回。"
    try:
        body, elapsed = call_meta(state, questions, model=args.model, key=key)
    except JevError as exc:
        print("[3] 调用失败: %s" % exc)
        return 1

    print("[3] 调用成功 latency=%.3fs model=%s" % (elapsed, body.get("model")))
    print(render_response(state, questions, body, elapsed))
    print()
    print("[4] 契约形状校验")
    ok = True
    checks = [
        ("choice 含 choice/confidence/probabilities",
         {"choice", "confidence", "probabilities"} <= set(body["answers"]["intent"])),
        ("score  含 score/legend/probabilities/confidence",
         {"score", "legend", "probabilities", "confidence"} <= set(body["answers"]["urgency"])),
        ("noul   只有 noul(无 confidence)",
         set(body["answers"]["need_human"]) - {"type"} == {"noul"}),
        ("顶层含 model/answers/usage",
         {"model", "answers", "usage"} <= set(body)),
    ]
    for name, passed in checks:
        ok &= passed
        print("    %-46s %s" % (name, "OK" if passed else "FAIL"))
    print()
    print("自检结果: %s" % ("PASS —— 可以直接用了" if ok else "FAIL —— 契约形状与预期不符,请提 issue"))
    print("下一步:python jev.py --state \"你的文本\" --ask \"你的问题?\" --choices a=说明,b=说明")
    return 0 if ok else 1


def _run_json(args):
    with open(args.json, encoding="utf-8") as fh:
        payload = json.load(fh)
    payload.setdefault("model", args.model)
    questions = payload.get("questions") or {}
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    body, elapsed = call_meta(payload["state"], questions, model=payload["model"],
                              key=args.key, timeout=args.timeout)
    if args.raw:
        print(json.dumps(body, ensure_ascii=False))
    else:
        print(render_response(payload["state"], questions, body, elapsed))
    return 0


def _run_jsonl(args):
    rows = []
    with open(args.jsonl, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                rows.append(json.loads(line))
    if not rows:
        print("空输入", file=sys.stderr)
        return 2

    payloads = [build_payload(r["state"], r["questions"], r.get("model", args.model)) for r in rows]
    if args.dry_run:
        print(json.dumps(payloads, ensure_ascii=False, indent=2))
        return 0

    key = api_key(args.key)

    def one(payload):
        t0 = time.perf_counter()
        try:
            body = call(payload["state"], payload["questions"], model=payload["model"],
                        key=key, timeout=args.timeout)
            return {"ok": True, "latency": round(time.perf_counter() - t0, 3),
                    "answers": body["answers"], "usage": body.get("usage")}
        except JevError as exc:
            return {"ok": False, "error": str(exc)}

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        results = list(pool.map(one, payloads))
    wall = time.perf_counter() - t0

    sink = open(args.out, "w", encoding="utf-8") if args.out else sys.stdout
    try:
        for row, res in zip(rows, results):
            rec = dict(res)
            rec["state"] = row["state"] if isinstance(row["state"], str) else json.dumps(row["state"], ensure_ascii=False)
            sink.write(json.dumps(rec, ensure_ascii=False) + "\n")
    finally:
        if args.out:
            sink.close()

    bad = sum(1 for r in results if not r["ok"])
    lat = sorted(r["latency"] for r in results if r["ok"])
    msg = "完成 %d 条 | 失败 %d | 总耗时 %.2fs | 并发 %d" % (len(results), bad, wall, args.workers)
    if lat:
        msg += " | p50 %.3fs" % lat[len(lat) // 2]
    if args.out:
        msg += " | 结果 -> %s" % args.out
    print(msg, file=sys.stderr)
    return 1 if bad else 0


def _run_single(args):
    state = _read_state(args)
    spec = _single_question(args)
    questions = {args.qid: spec}
    if args.dry_run:
        print(json.dumps(build_payload(state, questions, args.model), ensure_ascii=False, indent=2))
        return 0
    body, elapsed = call_meta(state, questions, model=args.model, key=args.key, timeout=args.timeout)
    if args.raw:
        print(json.dumps(body, ensure_ascii=False))
    else:
        print(render_response(state, questions, body, elapsed))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="jev.py",
        description="TypeSafe Jev / System One API 最小客户端 —— 只填 TYPESAFE_API_KEY 就能用",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="例:\n"
               "  python jev.py --selftest\n"
               "  python jev.py --state \"订单三天没发货\" --ask \"核心诉求?\" --choices refund=退款,ship=催发货\n"
               "  python jev.py --state \"...\" --ask \"紧急度?\" --score \"很低,低,中,高,很高\"\n"
               "  python jev.py --state \"...\" --ask \"要转人工吗?\" --noul\n"
               "  python jev.py --json payload.json\n"
               "  python jev.py --jsonl rows.jsonl -j 8 --out out.jsonl\n",
    )
    ap.add_argument("--selftest", action="store_true", help="自检:验证 key + 连通性 + 三类原语 + 契约形状")
    ap.add_argument("--state", help="待判断的状态;传 - 从 stdin 读")
    ap.add_argument("--state-file", help="从文件读 state")
    ap.add_argument("--state-json", help="state 是对象/数组时,直接给 JSON 文本")
    ap.add_argument("--ask", help="单个问题的问法(instructions)")
    ap.add_argument("--choices", help="choice 选项,如 'a=说明,b=说明'(省略 =说明 时用 key 当说明)")
    ap.add_argument("--score", help="score 档位,逗号分隔,2~10 个")
    ap.add_argument("--noul", action="store_true", help="问一个是/否问题")
    ap.add_argument("--qid", default="q", help="问题 id(默认 q)")
    ap.add_argument("--json", help="完整请求体 JSON 文件 ({state, model, questions})")
    ap.add_argument("--jsonl", help="批量:每行一个 {state, questions[, model]}")
    ap.add_argument("--out", help="批量结果输出文件(默认 stdout)")
    ap.add_argument("--workers", "-j", type=int, default=8, help="批量并发(默认 8;实测 10 并发无 429)")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="模型(默认 jev-latest)")
    ap.add_argument("--key", help="直接给 key(默认读环境变量;不建议写在命令行)")
    ap.add_argument("--timeout", type=float, default=60, help="单次超时秒数")
    ap.add_argument("--raw", action="store_true", help="只打印服务端原始 JSON(便于管道)")
    ap.add_argument("--dry-run", action="store_true", help="只打印请求体,不发网络请求")
    args = ap.parse_args(argv)

    try:
        if args.selftest:
            return _selftest(args)
        if args.json:
            return _run_json(args)
        if args.jsonl:
            return _run_jsonl(args)
        return _run_single(args)
    except JevError as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print("文件不存在: %s" % exc, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
