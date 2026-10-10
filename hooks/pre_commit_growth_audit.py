#!/usr/bin/env python3
"""lhg-user-growth 硬门①：git commit 前跑实验卡完整性审计，有 blocker 则拦截。

触发：PreToolUse / Bash。先判断本次 Bash 命令是否为 git commit，
不是则 0 开销直接放行；是则运行插件自带的 experiment_audit.py。

逃生方式（按推荐度排序）：
  1. 补齐实验卡缺项后重新 commit（推荐）。
  2. 紧急情况：LHG_UG_HOOKS_OFF=1 git commit -m "..."（单次豁免本次 hook）。
  3. /plugin disable lhg-user-growth（整个插件停用，hooks 不再触发）。

设计原则：脚本内部出错（找不到审计脚本、超时等）时 fail-open 直接放行，
不因插件自身故障骚扰用户；真正的门禁在 /lhg-user-growth:audit。
零第三方依赖。
"""

import json
import os
import re
import subprocess
import sys

AUDIT_TIMEOUT = 60
COMMIT_RE = re.compile(r"(^|[;&|])\s*git\s+.*\bcommit\b")


def main() -> int:
    # 逃生开关
    if os.environ.get("LHG_UG_HOOKS_OFF") == "1":
        return 0

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # 输入解析失败：fail-open

    tool_input = payload.get("tool_input", {}) or {}
    command = tool_input.get("command", "") or ""

    # 非 git commit：快速放行
    if not COMMIT_RE.search(command):
        return 0

    plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    audit_script = os.path.join(plugin_root, "scripts", "audit", "experiment_audit.py")
    if not os.path.isfile(audit_script):
        return 0  # 审计脚本缺失：fail-open，不拦截用户

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    try:
        proc = subprocess.run(
            [sys.executable, audit_script, "--target", project_dir, "--format", "json"],
            capture_output=True, text=True, timeout=AUDIT_TIMEOUT,
        )
        data = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except Exception:
        return 0  # 脚本失败：fail-open

    blockers = [f for f in data.get("findings", []) if f.get("severity") == "blocker"]
    if not blockers:
        return 0

    lines = [
        "提交被 lhg-user-growth 硬门拦截：实验卡审计发现 %d 个 blocker（缺假设/缺指标/缺动作这类硬伤），"
        "补齐再提交。" % len(blockers),
        "",
    ]
    for f in blockers[:10]:
        lines.append(
            "- [%s] %s:%s %s"
            % (f.get("rule_id"), f.get("file"), f.get("line"), f.get("title"))
        )
    if len(blockers) > 10:
        lines.append("…另有 %d 个，完整清单请跑 /lhg-user-growth:audit" % (len(blockers) - 10))
    lines += [
        "",
        "修复方式：运行 /lhg-user-growth:audit 按报告逐项补齐；",
        "紧急豁免（单次）：LHG_UG_HOOKS_OFF=1 git commit",
    ]
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "\n".join(lines),
        }
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
