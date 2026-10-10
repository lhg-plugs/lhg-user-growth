#!/usr/bin/env python3
"""lhg-user-growth 确定性实验卡审计：13 条规则，零第三方依赖。

扫描目标目录/文件的 markdown 实验卡，检查 8 要素完整性（假设/动作/指标/周期）、
指标口径一致性、复盘报告结构；有 blocker 时以 exit code 2 退出（供 hooks 与 CI 使用）。

用法：
    python3 experiment_audit.py --target <目录或文件> [--format json|text] [--fail-on blocker|warning]

规则文案均为本项目原创（方法论灵感见 ATTRIBUTION.md，未复制任何第三方原文）。
"""

import argparse
import json
import os
import re
import sys

VERSION = "1.0.0"
TOOL = "lhg-user-growth/experiment-audit"

SKIP_DIRS = {
    "node_modules", ".next", "dist", "build", ".git", "coverage",
    "__pycache__", "vendor", ".turbo", "out", "fixtures",
}


class Finding:
    __slots__ = ("rule_id", "severity", "category", "title", "file", "line", "snippet", "detail")

    def __init__(self, rule_id, severity, category, title, file, line, snippet, detail):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.title = title
        self.file = file
        self.line = line
        self.snippet = snippet
        self.detail = detail

    def to_dict(self):
        return {
            "rule_id": self.rule_id, "severity": self.severity,
            "category": self.category, "title": self.title,
            "file": self.file, "line": self.line,
            "snippet": self.snippet, "detail": self.detail,
        }


def collect_files(target):
    if os.path.isfile(target):
        return [target] if target.endswith(".md") else []
    out = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".md"):
                out.append(os.path.join(root, f))
    return sorted(out)


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


# ---------------------------------------------------------------- 解析
CARD_RE = re.compile(r"^##\s+(.+)$")
SECTION_RE = re.compile(r"^#{2,4}\s*(.+)$")


def split_cards(lines):
    """按 ## 标题切出实验卡；只保留疑似实验卡的块（标题含 实验/E+数字）。"""
    cards = []
    cur = None
    for i, ln in enumerate(lines):
        m = CARD_RE.match(ln)
        if m:
            if cur:
                cards.append(cur)
            cur = {"title": m.group(1).strip(), "start": i + 1, "lines": []}
        elif cur is not None:
            cur["lines"].append((i + 1, ln))
    if cur:
        cards.append(cur)
    out = []
    for c in cards:
        t = c["title"]
        if "实验" in t or re.search(r"\bE\d+\b", t, re.I):
            out.append(c)
    return out


def section_text(card, *keywords):
    """取卡内某小节（### 假设 / ### 指标 等）的正文；找不到返回 ''。"""
    buf, hit = [], False
    for _, ln in card["lines"]:
        m = SECTION_RE.match(ln)
        if m:
            hit = any(k in m.group(1) for k in keywords)
            continue
        if hit:
            buf.append(ln)
    return "\n".join(buf)


def card_text(card):
    return "\n".join(ln for _, ln in card["lines"])


def has_kw(text, *kws):
    return any(k in text for k in kws)


# ---------------------------------------------------------------- 规则定义

RULES = []
_RULE_BY_ID = {}


def rule(rule_id, severity, category, title, detail):
    def deco(fn):
        r = {"id": rule_id, "severity": severity, "category": category,
             "title": title, "detail": detail}
        _RULE_BY_ID[rule_id] = r
        r["check"] = fn
        RULES.append(r)
        return fn
    return deco


def _mk(rule_id, path, line, snippet):
    r = _RULE_BY_ID[rule_id]
    return Finding(r["id"], r["severity"], r["category"], r["title"],
                   path, line, snippet[:160], r["detail"])


# ---------------- 完整性 ----------------

@rule("UG-CMP-001", "blocker", "完整性", "实验卡缺少「假设」",
      "没有假设的实验等于瞎试。按\"如果…那么…因为…\"句式补上假设。")
def r_cmp_001(card, text, path, ctx):
    if not has_kw(text, "假设"):
        return [_mk("UG-CMP-001", path, card["start"], card["title"])]
    return []


@rule("UG-CMP-002", "blocker", "完整性", "实验卡缺少「成功指标」",
      "没有成功指标，跑完不知道算赢算输。定 1 个主指标 + 口径定义。")
def r_cmp_002(card, text, path, ctx):
    if not has_kw(text, "指标", "成功标准", "目标"):
        return [_mk("UG-CMP-002", path, card["start"], card["title"])]
    return []


@rule("UG-CMP-003", "blocker", "完整性", "实验卡缺少「动作」",
      "动作没写具体，等于没法执行。写清谁、在哪、做什么。")
def r_cmp_003(card, text, path, ctx):
    if not has_kw(text, "动作", "执行", "怎么做", "步骤"):
        return [_mk("UG-CMP-003", path, card["start"], card["title"])]
    return []


@rule("UG-CMP-004", "warning", "完整性", "实验卡缺少「周期」",
      "没有截止日的实验永远\"还在跑\"。定 N 天 + 起止日期。")
def r_cmp_004(card, text, path, ctx):
    if not has_kw(text, "周期", "时长", "天", "周", "日期"):
        return [_mk("UG-CMP-004", path, card["start"], card["title"])]
    return []


@rule("UG-CMP-005", "warning", "完整性", "实验卡缺少「负责人」",
      "写\"大家一起\"等于没人负责。指定 1 个人名。")
def r_cmp_005(card, text, path, ctx):
    if not has_kw(text, "负责人", "负责", "分工", "owner"):
        return [_mk("UG-CMP-005", path, card["start"], card["title"])]
    return []


@rule("UG-CMP-006", "warning", "完整性", "实验卡缺少优先级评分",
      "没有 ICE/优先级评分，实验顺序就是拍脑袋。补 I/C/E 打分与理由。")
def r_cmp_006(card, text, path, ctx):
    if not has_kw(text, "ICE", "优先级", "评分", "排序"):
        return [_mk("UG-CMP-006", path, card["start"], card["title"])]
    return []


@rule("UG-ID-001", "warning", "完整性", "实验卡未编号",
      "标题无编号（如 E1），多实验并行时无法追踪。按 E1/E2…编号。")
def r_id_001(card, text, path, ctx):
    if not re.search(r"E\d+|实验\s*\d+|实验\s*[一二三四五]", card["title"]):
        return [_mk("UG-ID-001", path, card["start"], card["title"])]
    return []


# ---------------- 假设质量 ----------------

@rule("UG-HYP-001", "blocker", "假设质量", "假设缺少因果句式",
      "假设段无\"如果\"/\"因为\"等因果词，大概率是拍脑袋。按\"如果…那么…因为…\"重写。")
def r_hyp_001(card, text, path, ctx):
    hyp = section_text(card, "假设")
    if not hyp:
        hyp = text  # 无独立小节时退化为整卡检查
    if not has_kw(hyp, "如果", "因为", "由于", "导致"):
        return [_mk("UG-HYP-001", path, card["start"],
                    (hyp.strip().split("\n")[0] if hyp.strip() else card["title"]))]
    return []


# ---------------- 指标口径 ----------------

NUM_RE = re.compile(r"\d+(?:\.\d+)?\s*[%％]|(?:[\d,]+\.?\d*)\s*(人|次|元|单|个|天|周)")


@rule("UG-MET-001", "blocker", "指标口径", "指标无基线与目标数字",
      "成功指标没有\"基线→目标\"数字，跑完无法判定输赢。补上数字；无数据写\"无基线，先测 7 天\"。")
def r_met_001(card, text, path, ctx):
    met = section_text(card, "指标", "成功标准")
    if not met:
        met = text
    nums = NUM_RE.findall(met)
    if len(nums) < 2 and "无基线" not in met:
        return [_mk("UG-MET-001", path, card["start"],
                    (met.strip().split("\n")[0] if met.strip() else card["title"]))]
    return []


VANITY_RES = ["阅读量", "粉丝", "点赞", "播放量", "曝光", "下载量"]
REAL_RES = ["转化", "留存", "付费", "注册", "激活", "复购", "下单", "使用", "回访"]


@rule("UG-MET-002", "warning", "指标口径", "疑似虚荣指标",
      "指标只提阅读量/粉丝/点赞等，未见转化/留存/付费类指标。热闹不等于增长，请加 1 个转化类指标。")
def r_met_002(card, text, path, ctx):
    met = section_text(card, "指标", "成功标准")
    if not met:
        return []
    if has_kw(met, *VANITY_RES) and not has_kw(met, *REAL_RES):
        return [_mk("UG-MET-002", path, card["start"],
                    met.strip().split("\n")[0][:160])]
    return []


@rule("UG-MET-003", "warning", "指标口径", "复盘指标与实验指标疑似不一致",
      "复盘段提到的指标名在实验指标段未出现。复盘必须用同一口径，否则结论作废。")
def r_met_003(card, text, path, ctx):
    met = section_text(card, "指标", "成功标准")
    rev = section_text(card, "复盘")
    if not met or not rev:
        return []
    metric_names = [m for m in set(re.findall(r"[转化留存付费注册激活复购下单回访分享]{2,}率?", met)) if len(m) >= 2]
    rev_metrics = set(re.findall(r"[转化留存付费注册激活复购下单回访分享]{2,}率?", rev))
    if rev_metrics and not (set(metric_names) & rev_metrics):
        return [_mk("UG-MET-003", path, card["start"],
                    "指标段：%s；复盘段：%s" % (
                        "、".join(sorted(set(metric_names))[:3]),
                        "、".join(sorted(rev_metrics)[:3])))]
    return []


# ---------------- 复盘结构 ----------------

@rule("UG-REV-001", "blocker", "复盘结构", "复盘缺少结论",
      "有复盘段但无\"结论\"（成立/证伪/无法判断）。没结论的复盘等于没复盘。")
def r_rev_001(card, text, path, ctx):
    rev = section_text(card, "复盘")
    if rev and not has_kw(rev, "结论", "成立", "证伪", "无法判断"):
        return [_mk("UG-REV-001", path, card["start"],
                    rev.strip().split("\n")[0][:160] if rev.strip() else card["title"])]
    return []


@rule("UG-REV-002", "warning", "复盘结构", "复盘缺少下一步动作",
      "复盘无\"下一步\"/\"后续\"/\"放大\"/\"补实验\"。结论必须配动作，否则复盘白做。")
def r_rev_002(card, text, path, ctx):
    rev = section_text(card, "复盘")
    if rev and not has_kw(rev, "下一步", "后续", "放大", "补实验", "继续", "停止"):
        return [_mk("UG-REV-002", path, card["start"],
                    rev.strip().split("\n")[0][:160] if rev.strip() else card["title"])]
    return []


# ---------------------------------------------------------------- 运行器

def run(target):
    files = collect_files(target)
    findings = []
    for path in files:
        text = read_text(path)
        lines = text.split("\n")
        rel = os.path.relpath(path, os.path.abspath(target) if os.path.isdir(target)
                              else os.path.dirname(os.path.abspath(target)))
        for card in split_cards(lines):
            ctext = card_text(card)
            for r in RULES:
                try:
                    for f in r["check"](card, ctext, path, {}) or []:
                        f.file = rel
                        findings.append(f)
                except Exception:
                    continue  # 单条规则异常不影响整体
    return files, findings


def main(argv=None):
    ap = argparse.ArgumentParser(description="lhg-user-growth 确定性实验卡审计")
    ap.add_argument("--target", default=".", help="扫描目录或文件")
    ap.add_argument("--format", choices=["json", "text"], default="text")
    ap.add_argument("--fail-on", choices=["blocker", "warning"], default="blocker")
    args = ap.parse_args(argv)

    target = os.path.abspath(args.target)
    if not (os.path.isdir(target) or os.path.isfile(target)):
        print("target 不存在：%s" % args.target, file=sys.stderr)
        return 1

    files, findings = run(target)
    sev_rank = {"blocker": 2, "warning": 1}
    counts = {"blocker": 0, "warning": 0}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    result = {
        "tool": TOOL,
        "version": VERSION,
        "target": args.target,
        "summary": {
            "files_scanned": len(files),
            "rules_run": len(RULES),
            "blocker": counts["blocker"],
            "warning": counts["warning"],
        },
        "findings": [f.to_dict() for f in sorted(
            findings, key=lambda x: (-sev_rank.get(x.severity, 0), x.file, x.line))],
    }

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        s = result["summary"]
        print("实验卡审计：扫描 %d 文件，运行 %d 条规则" % (s["files_scanned"], s["rules_run"]))
        print("blocker=%d warning=%d" % (s["blocker"], s["warning"]))
        for f in result["findings"]:
            print("[%s][%s] %s:%d %s" % (
                f["severity"].upper(), f["rule_id"], f["file"], f["line"], f["title"]))
            print("    %s" % f["detail"])
            if f["snippet"]:
                print("    → %s" % f["snippet"])

    level = sev_rank[args.fail_on]
    bad = any(sev_rank.get(f.severity, 0) >= level for f in findings)
    return 2 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
