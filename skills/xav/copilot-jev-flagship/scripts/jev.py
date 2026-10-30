import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

URL = "https://copilot.tencent.com/v2/systemone"
SAMPLE = {
    "state": {"ticket": "My invoice is wrong; please help today."},
    "questions": {
        "urgent": {"instructions": "Is this urgent?", "noul": {}},
        "team": {
            "instructions": "Who should help?",
            "choice": {"criteria": {"billing": "Invoices", "support": "Support"}},
        },
        "level": {
            "instructions": "How urgent?",
            "score": {"criteria": ["routine", "urgent"]},
        },
    },
}


def credential(path):
    if path:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        values = [line.split("=", 1)[1].strip() for line in lines if line.startswith("jwt=")]
        token = values[0] if len(values) == 1 else ""
    else:
        token = os.environ.get("JEV_JWT", "").strip()
        if not token:
            if not sys.stdin.isatty():
                raise ValueError("请在终端隐藏输入 pt_ 凭据，或指定 --env-file /绝对路径/.env")
            token = getpass.getpass("Copilot JWT (pt_...): ").strip()
    if not token.startswith("pt_") or any(char.isspace() for char in token):
        raise ValueError("凭据必须是 pt_ 开头的 Copilot JWT / 会话令牌；不要使用 ck_ 或 apikey_ 凭据")
    return token


def payload(path):
    value = json.loads(Path(path).read_text(encoding="utf-8")) if path else SAMPLE
    if not isinstance(value, dict) or not value.get("state") or not isinstance(value.get("questions"), dict) or not value["questions"]:
        raise ValueError("输入必须是非空的 state 和 questions 组成的 JSON 对象")
    return {"model": "jev", "stream": False, "system_one": value}


def call(token, body):
    conversation = str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "CodeBuddyIDE/4.9.7 CodeBuddy/4.9.7",
        "X-Conversation-ID": conversation,
        "X-Conversation-Request-ID": request_id,
        "X-Conversation-Message-ID": str(uuid.uuid4()),
        "X-Request-ID": request_id,
        "X-IDE-Type": "vscode",
        "X-IDE-Name": "vscode",
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(URL, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            status = response.status
            result = json.load(response)
    except urllib.error.HTTPError as error:
        try:
            result = json.load(error)
        except (ValueError, UnicodeError):
            result = {}
        raise ValueError(f"HTTP {error.code}: code={result.get('code')} msg={result.get('msg')} requestId={result.get('requestId')}") from None
    if status != 200 or not isinstance(result, dict) or result.get("type") != "systemone.answers.done" or result.get("model") != "jev" or not isinstance(result.get("answers"), dict):
        raise ValueError("服务端返回值不符合 Jev System One 成功格式")
    return result


def main():
    parser = argparse.ArgumentParser(description="内领旗舰版 Copilot Jev 极简调用")
    parser.add_argument("--env-file", help="明确指定含 jwt=pt_... 的本地文件")
    parser.add_argument("--input", help="仅含 state 与 questions 的 JSON 文件；默认使用内置三题演示")
    args = parser.parse_args()
    try:
        result = call(credential(args.env_file), payload(args.input))
    except (ValueError, OSError, urllib.error.URLError) as error:
        print(f"调用失败：{error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
