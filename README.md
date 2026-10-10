<!-- About 简介（推送后填写到仓库 About 栏）：
小白可执行的增长实验清单：从杠杆诊断到复盘 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-user-growth
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, growth-hacking, marketing -->

# lhg-user-growth：小白可执行的增长实验清单

> **一句话介绍**：给 AI 助手装上"用户增长专家"——AARRR 漏斗诊断找出增长杠杆，生成带假设/动作/指标/周期的可执行实验清单，13 条确定性规则校验完整性，实验跑完按模板复盘。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-user-growth
> /plugin install lhg-user-growth@lhg-plugs
> ```

## 它是什么

`lhg-user-growth` 是一个 Claude Code 插件（plugin 为主、skill 为辅），面向**不懂增长方法论的小白**：

- **4 个命令**（小白入口）：`growth` 增长全流程（诊断→实验清单→复盘模板），`levers` 增长杠杆库（按 AARRR 环节挑点子），`experiment` 单张实验卡生成/复盘，`audit` 实验清单体检
- **4 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：AARRR 漏斗诊断、实验清单设计、增长复盘、指标口径
- **3 个专家 agent**：增长策略师、实验评审、指标守门员
- **2 个硬门 hooks**：commit 前实验卡审计拦截、写实验卡缺项提醒（均可一键豁免）
- **13 条确定性校验规则**：纯 Python、零第三方依赖，秒级出结果

需要严格的 A/B 实验设计（分组/样本量/显著性判定/p-hacking 防护）时，转交兄弟插件 `lhg-growth-lab`——两个插件互链，不重复造轮子。

## 4 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-user-growth:growth` | 增长全流程：产品输入→漏斗诊断→实验清单→复盘模板 | `/lhg-user-growth:growth "做个小区团购小程序"` |
| `/lhg-user-growth:levers` | 增长杠杆库：按 AARRR 五环节浏览杠杆与最小实验点子 | `/lhg-user-growth:levers 留存` |
| `/lhg-user-growth:experiment` | 单张实验卡：生成（含假设/动作/指标/周期）或复盘 | `/lhg-user-growth:experiment "注册页加视频"` |
| `/lhg-user-growth:audit` | 实验清单体检：完整性/口径一致性/复盘结构校验 | `/lhg-user-growth:audit docs/` |

## 自查说明

自查 = 确定性脚本（机器）+ 人工评审清单（人）：

1. 先跑 `scripts/audit/experiment_audit.py`（13 条规则），零 LLM 成本；
2. 发现分两级：**blocker**（缺假设/缺成功指标/缺动作/复盘缺结论，必须补，commit 前 hook 会拦截）、**warning**（缺周期/缺负责人/虚荣指标/口径不一致，补上或写豁免理由）；
3. 再按 `lhg-ug-experiments` 第 6 节人工评审清单过一遍脚本抓不到的（假设的因果是否成立、基线来源是否可信、同期实验是否互斥）。

blocker 清零才算做完；为清零改规则算作弊，不许。

## 目录结构

```
lhg-user-growth/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 4 个命令：growth / levers / experiment / audit
├── skills/                  # 4 个平台中立 skill（diagnose/experiments/review/metrics）
├── agents/                  # 3 个专家 agent（growth-strategist / experiment-reviewer / metric-guardian）
├── hooks/                   # 2 个硬门（commit 前审计拦截 / 实验卡缺项提醒）+ 豁免说明
├── scripts/audit/           # 13 条确定性校验规则（零第三方依赖）
├── fixtures/                # 冒烟测试用例（坏/好对照）
├── smoke_test.py            # 一键冒烟测试
├── ATTRIBUTION.md           # 灵感来源与许可声明
└── LICENSE                  # MIT
```

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 产品有用户但增长停滞，不知道先优化哪个环节 → 用 `/lhg-user-growth:growth` 做漏斗诊断
- 脑子里有 10 个增长点子，排不出优先级 → 用 ICE 打分 + 实验卡模板排出来
- 实验跑完说不清赢没赢 → 用 `/lhg-user-growth:experiment E1 复盘` 按三态结论复盘
- 团队各说各话，"增长了"指的不是一件事 → 用 `lhg-ug-metrics` 定北极星 + 写口径文档

**什么时候不用：**

- 产品还没上线、没有用户数据 → 先做冷启动，漏斗诊断需要至少有一个环节的数据
- 需要严格的统计显著性（p 值/置信区间/样本量计算）→ 用兄弟插件 `lhg-growth-lab`，本插件只做轻量实验
- 你已经有成熟的增长团队和方法论 → 本插件是给小白搭的脚手架，重度用户会觉得浅

## lhg-plugs 插件矩阵

| 插件 | 一句话 | 安装 |
|---|---|---|
| [lhg-user-growth](https://github.com/lhg-plugs/lhg-user-growth) | 小白可执行的增长实验清单：从杠杆诊断到复盘 | `/plugin install lhg-user-growth@lhg-plugs` |
| [lhg-growth-lab](https://github.com/lhg-plugs/lhg-growth-lab) | 增长实验专家：假设→实验设计→显著性判定→防 p-hacking | `/plugin install lhg-growth-lab@lhg-plugs` |
| [lhg-fullstack](https://github.com/lhg-plugs/lhg-fullstack) | 小白一句话 → 高质量全栈应用 | `/plugin install lhg-fullstack@lhg-plugs` |

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（JSON 合法、skill/command/agent 完整性、13 条规则、fixtures 命中、hooks 行为）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-user-growth/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 视频号：搜「刘洪光实名上网」
- 微信：lhgsmsw
