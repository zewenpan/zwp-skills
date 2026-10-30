#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jev.py 的离线回归测试 —— 不需要 API key,不需要联网。

    python tests/test_jev.py

三组验证:
  A. 契约重放   用 examples/real_io.json 里的 26 组真实历史请求/响应,
                校验 build_payload 能原样重建当年的请求体,render 能吃掉当年的响应体。
                (即:客户端与真实契约零漂移)
  B. HTTP 层    起一个本地 mock server,把 urlopen 的整条链路走一遍:
                header 注入、401/400 异常分类、5xx 退避重试、批量顺序保持。
  C. CLI 契约   --dry-run 的产物必须是合法且完整的请求体;缺 key 必须给人话。
"""

import json
import os
import sys
import threading
import time
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))

import jev  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    show = ("  <- " + str(detail)[:220]) if (not cond and detail != "" and detail is not None) else ""
    print("  %-4s %s%s" % ("OK" if cond else "FAIL", name, show))


# ============================================================ A. 契约重放
def test_replay_recorded_io():
    print("\n[A] 用真实历史 IO 重放契约")
    path = ROOT / "examples" / "real_io.json"
    if not path.exists():
        check("examples/real_io.json 存在", False, path)
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data["results"] if isinstance(data, dict) else data

    n_req = n_ans = 0
    for item in items:
        io = item["io"]
        stages = {"": io} if "request" in io else io
        for stage_name, stage in stages.items():
            req, resp = stage["request"], stage["response"]
            # 1) 请求体可被原样重建
            rebuilt = jev.build_payload(req["state"], req["questions"], req["model"])
            check("%s%s 请求体重建一致" % (item["id"], (":" + stage_name) if stage_name else ""),
                  rebuilt == req, json.dumps(rebuilt, ensure_ascii=False)[:200] if rebuilt != req else "")
            n_req += 1
            # 2) 当年那批响应今天照样能被解析 + 渲染
            try:
                text = jev.render_response(req["state"], req["questions"], resp, 0.6)
                n_ans += len(resp["answers"])
                ok = all(qid in resp["answers"] for qid in req["questions"])
            except Exception as exc:  # noqa: BLE001
                ok, text = False, exc
            check("%s%s 响应可解析可渲染" % (item["id"], (":" + stage_name) if stage_name else ""), ok, text)

    print("  -> 重放 %d 个请求体 / %d 个 answer" % (n_req, n_ans))


def test_score_semantics():
    print("\n[A2] score 语义(浮点下标 -> legend 档位名)")
    ans = {"type": "score", "score": 3.12, "confidence": 0.9,
           "legend": {"0": "可忽略", "1": "轻微", "2": "中等", "3": "严重", "4": "不可逆"}}
    check("3.12 -> 严重", jev.score_label(ans) == "严重", jev.score_label(ans))
    check("0.02 -> 第一档", jev.score_label({"score": 0.02, "legend": ans["legend"]}) == "可忽略")
    check("4.0  -> 末档", jev.score_label({"score": 4.0, "legend": ans["legend"]}) == "不可逆")
    check("越界 clamp", jev.score_label({"score": 9.9, "legend": ans["legend"]}) == "不可逆")
    check("无 legend 返回 None", jev.score_label({"score": 1}) is None)


# ============================================================== B. HTTP 层
class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # 静音
        pass

    def _send(self, status, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        srv = self.server
        srv.hits.append({"method": "GET", "path": self.path,
                         "auth": self.headers.get("Authorization")})
        self._send(200, {"data": [{"id": "jev-latest"}, {"id": "jev-preview"}]})

    def do_POST(self):
        srv = self.server
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:  # noqa: BLE001
            payload = None
        srv.hits.append({"method": "POST", "path": self.path,
                         "auth": self.headers.get("Authorization"),
                         "ctype": self.headers.get("Content-Type"), "payload": payload})
        # script 里每一项是 (status, body);body=None 且 status=200 表示「走默认成功响应」
        scripted = srv.script.pop(0) if srv.script else None
        if scripted is not None:
            status, body = scripted
            if body is None:
                body = None if status == 200 else {"error": "scripted"}
            if body is not None:
                self._send(status, body)
                return
        answers = {}
        for qid, q in ((payload or {}).get("questions") or {}).items():
            if q["type"] == "choice":
                crit = q.get("criteria") or {}
                keys = list(crit) if isinstance(crit, dict) else list(crit)
                first = keys[0] if keys else "x"
                answers[qid] = {"type": "choice", "choice": first, "confidence": 0.9,
                                "probabilities": {k: (1.0 if k == first else 0.0) for k in (keys or ["x"])}}
            elif q["type"] == "score":
                n = len(q.get("criteria") or [])
                answers[qid] = {"type": "score", "score": 0.0, "confidence": 1.0,
                                "legend": {str(i): v for i, v in enumerate(q["criteria"])},
                                "probabilities": {str(i): (1.0 if i == 0 else 0.0) for i in range(n)}}
            else:
                answers[qid] = {"type": "noul", "noul": 0.5}
        self._send(200, {"model": "jev-mock-1.0", "answers": answers,
                         "usage": {"input_tokens": 10, "output_tokens": 4}})


def _serve(script=None):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    srv.hits, srv.script = [], list(script or [])
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % srv.server_address[1]
    jev.SYSTEMONE_URL = base + "/v1/systemone"
    jev.MODELS_URL = base + "/v1/models"
    return srv, base


def test_http_layer():
    print("\n[B] HTTP 层(本地 mock server)")
    srv, _ = _serve()
    os.environ["TYPESAFE_API_KEY"] = "apikey_test_123"

    try:
        body, elapsed = jev.call_meta("test", {"q": {"type": "noul", "instructions": "?"}})
        hit = srv.hits[-1]
        check("POST 到 /v1/systemone", hit["path"] == "/v1/systemone", hit["path"])
        check("Bearer 头注入", hit["auth"] == "Bearer apikey_test_123", hit["auth"])
        check("Content-Type 正确", hit["ctype"] == "application/json", hit["ctype"])
        check("中文不被转义丢失", hit["payload"]["state"] == "test")
        check("有 usage", body["usage"]["input_tokens"] == 10)
        check("elapsed 是正数", isinstance(elapsed, float) and elapsed >= 0)
    except Exception as exc:  # noqa: BLE001
        check("基础调用链路", False, exc)

    # 401 -> JevAuthError,且不重试
    srv.script = [(401, {"error": "invalid key"})]
    try:
        jev.call("x", {"q": {"type": "noul", "instructions": "?"}}, retries=3)
        check("401 抛 JevAuthError", False, "没抛")
    except jev.JevAuthError:
        check("401 抛 JevAuthError", True)
    except Exception as exc:  # noqa: BLE001
        check("401 抛 JevAuthError", False, exc)

    # 400 -> JevHTTPError(status=400),且不重试
    srv.script = [(400, {"error": {"code": "api_usage_error"}})]
    before = len(srv.hits)
    try:
        jev.call("x", {"q": {"type": "noul", "instructions": "?"}}, retries=3)
        check("400 抛 JevHTTPError", False, "没抛")
    except jev.JevHTTPError as exc:
        check("400 抛 JevHTTPError", exc.status == 400, exc.status)
    except Exception as exc:  # noqa: BLE001
        check("400 抛 JevHTTPError", False, exc)
    check("400 不重试(只打一次)", len(srv.hits) - before == 1, len(srv.hits) - before)

    # 500 -> 重试后成功
    srv.script = [(500, {"error": "boom"}), (200, None)]
    before = len(srv.hits)
    try:
        jev.call("x", {"q": {"type": "noul", "instructions": "?"}}, retries=3)
        check("500 退避后重试成功", True)
        check("确实重试了(打了 2 次)", len(srv.hits) - before == 2, len(srv.hits) - before)
    except Exception as exc:  # noqa: BLE001
        check("500 退避后重试成功", False, exc)

    # list_models
    try:
        m = jev.list_models()
        check("GET /v1/models 可用", m["data"][0]["id"] == "jev-latest")
        check("GET 也带 Bearer", srv.hits[-1]["auth"] == "Bearer apikey_test_123")
    except Exception as exc:  # noqa: BLE001
        check("GET /v1/models 可用", False, exc)

    # batch:顺序必须与入参一致
    srv.script = []
    states = ["s%d" % i for i in range(12)]
    qs = {"q": {"type": "noul", "instructions": "?"}}
    try:
        out = jev.batch(states, qs, workers=6)
        check("batch 条数正确", len(out) == 12, len(out))
        check("batch 顺序保持", [s for s, _ in out] == states)
        check("batch 返回完整 answers 映射", all(a.get("q", {}).get("noul") == 0.5 for _, a in out),
              [a for _, a in out if a.get("q", {}).get("noul") != 0.5][:2])
    except Exception as exc:  # noqa: BLE001
        check("batch 顺序保持", False, exc)

    # on_error="skip"
    srv.script = [(400, {"error": "bad"}), (400, {"error": "bad"})]
    try:
        out = jev.batch(["a", "b"], qs, workers=1, on_error="skip")
        check('on_error="skip" 不抛', all("error" in a for _, a in out), out)
    except Exception as exc:  # noqa: BLE001
        check('on_error="skip" 不抛', False, exc)

    srv.shutdown()


def test_input_validation():
    print("\n[B2] 入参校验(本地拦截,不浪费调用)")
    bad = [
        ("空 questions", lambda: jev.build_payload("s", {})),
        ("question 不是 dict", lambda: jev.build_payload("s", {"q": "choice"})),
        ("非法 type", lambda: jev.build_payload("s", {"q": {"type": "freeform"}})),
        ("缺 type", lambda: jev.build_payload("s", {"q": {"instructions": "?"}})),
        ("score 只给 1 档", lambda: jev.ask_score("s", "?", ["a"])),
        ("score 给 11 档", lambda: jev.ask_score("s", "?", list("abcdefghijk"))),
    ]
    for name, fn in bad:
        try:
            fn()
            check(name + " -> 被拦截", False, "没抛")
        except jev.JevError:
            check(name + " -> 被拦截", True)
        except Exception as exc:  # noqa: BLE001
            check(name + " -> 被拦截", False, exc)


# ============================================================== C. CLI 契约
def test_cli():
    print("\n[C] CLI 契约(--dry-run,不发网络)")
    import io
    from contextlib import redirect_stdout

    def run(argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = jev.main(argv)
        return rc, buf.getvalue()

    rc, out = run(["--dry-run", "--state", "订单三天没发货",
                   "--ask", "核心诉求?", "--choices", "refund=退款,ship=催发货"])
    try:
        body = json.loads(out)
        check("--choices 产物是合法 JSON", True)
        check("state 正确", body["state"] == "订单三天没发货")
        check("model 有默认值", body["model"] == "jev-latest")
        check("criteria 是 dict 且 key=返回值",
              body["questions"]["q"]["criteria"] == {"refund": "退款", "ship": "催发货"})
    except Exception as exc:  # noqa: BLE001
        check("--choices 产物是合法 JSON", False, "%s | %s" % (exc, out[:200]))

    rc, out = run(["--dry-run", "--state", "x", "--ask", "紧急度?", "--score", "很低,低,中,高,很高"])
    body = json.loads(out)
    check("--score 产出 list criteria",
          body["questions"]["q"]["criteria"] == ["很低", "低", "中", "高", "很高"], body["questions"]["q"])

    rc, out = run(["--dry-run", "--state", "x", "--ask", "要转人工吗?", "--noul"])
    body = json.loads(out)
    check("--noul 无 criteria", "criteria" not in body["questions"]["q"] and body["questions"]["q"]["type"] == "noul")

    rc, out = run(["--dry-run", "--state-json", '{"a":1,"b":[2,3]}', "--ask", "?", "--noul"])
    body = json.loads(out)
    check("--state-json 支持对象 state", body["state"] == {"a": 1, "b": [2, 3]})

    rc, out = run(["--dry-run", "--state", "x", "--ask", "?", "--choices", "a,b"])
    body = json.loads(out)
    check("--choices 省略说明时 key 兼作说明", body["questions"]["q"]["criteria"] == {"a": "a", "b": "b"})

    rc, out = run(["--state", "x", "--ask", "?", "--choices", "a,b", "--noul"])
    check("三类原语互斥被拦截", rc == 1, rc)

    # 批量 dry-run
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as fh:
        fh.write(json.dumps({"state": "a", "questions": {"q": {"type": "noul", "instructions": "?"}}}, ensure_ascii=False) + "\n")
        fh.write(json.dumps({"state": "b", "questions": {"q": {"type": "choice", "instructions": "?",
                                                              "criteria": {"x": "X"}}}}, ensure_ascii=False) + "\n")
        jsonl = fh.name
    rc, out = run(["--jsonl", jsonl, "--dry-run"])
    try:
        arr = json.loads(out)
        check("--jsonl 逐行转请求体", len(arr) == 2 and arr[0]["state"] == "a")
    except Exception as exc:  # noqa: BLE001
        check("--jsonl 逐行转请求体", False, "%s | %s" % (exc, out[:200]))
    os.unlink(jsonl)

    # 缺 key 时的人话提示
    saved = {n: os.environ.pop(n, None) for n in jev.ENV_VARS}
    try:
        err, out = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = jev.main(["--selftest"])
        txt = err.getvalue() + out.getvalue()
        check("--selftest 缺 key 返回码 2", rc == 2, rc)
        check("缺 key 提示含环境变量名", "TYPESAFE_API_KEY" in txt, txt[:160])
    finally:
        for n, v in saved.items():
            if v is not None:
                os.environ[n] = v

    # JEV_API_KEY 作为备用变量名
    os.environ.pop("TYPESAFE_API_KEY", None)
    os.environ["JEV_API_KEY"] = "apikey_backup"
    try:
        check("JEV_API_KEY 可作为替代变量", jev.api_key() == "apikey_backup")
    finally:
        os.environ.pop("JEV_API_KEY", None)


def main():
    t0 = time.time()
    print("=" * 68)
    print("jev.py 离线自检(不需要 API key / 不需要联网)")
    print("=" * 68)
    test_replay_recorded_io()
    test_score_semantics()
    test_http_layer()
    test_input_validation()
    test_cli()
    print("\n" + "=" * 68)
    print("通过 %d 项,失败 %d 项,耗时 %.2fs" % (len(PASS), len(FAIL), time.time() - t0))
    if FAIL:
        print("失败清单:")
        for f in FAIL:
            print("  - " + f)
    print("=" * 68)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
