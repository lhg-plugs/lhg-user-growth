#!/usr/bin/env python3
"""lhg-user-growth 硬门②（警告级，不拦截）：写实验卡 markdown 时检查 8 要素缺项。

触发：PostToolUse / Write|Edit。只做提醒，永远 exit 0、不拦截写入。
只检查疑似实验卡的文件（路径或内容含"实验"字样），其他 markdown 快速放行。

逃生方式：LHG_UG_HOOKS_OFF=1（环境变量）可关闭本提醒；
或 /plugin disable lhg-user-growth 停用整个插件。
零第三方依赖。
"""

import json
import os
import sys

REQUIRED = ("假设", "动作", "指标", "周期")
OPTIONAL = ("负责人", "复盘")


def looks_like_experiment_card(path, text):
    p = path.replace("\\", "/").lower()
    if any(k in p for k in ("实验", "experiment", "growth")):
        return True
    return "实验" in text[:2000] and any(k in text for k in ("假设", "成功指标"))


def main() -> int:
    if os.environ.get("LHG_UG_HOOKS_OFF") == "1":
        return 0

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    tool_input = payload.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "") or ""
    if not file_path:
        return 0
    if not file_path.endswith(".md"):
        return 0

    try:
        with open(file_path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return 0

    if not looks_like_experiment_card(file_path, text):
        return 0  # 非实验卡：快速放行

    missing = [k for k in REQUIRED if k not in text]
    missing_opt = [k for k in OPTIONAL if k not in text]
    if not missing and not missing_opt:
        return 0

    parts = []
    if missing:
        parts.append("缺失要素：%s（实验卡 8 要素不全，交付前请补齐）" % "、".join(missing))
    if missing_opt:
        parts.append("建议补充：%s" % "、".join(missing_opt))
    parts.append("交付前跑：/lhg-user-growth:audit；关闭本提醒：export LHG_UG_HOOKS_OFF=1。")
    msg = "实验卡提醒（lhg-user-growth）：%s\n%s" % (file_path, "\n".join(parts))
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": msg,
        }
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
