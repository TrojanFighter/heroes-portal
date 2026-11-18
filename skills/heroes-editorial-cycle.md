---
name: heroes-editorial-cycle
description: Weekly editorial-lane cycle for IndieGameLegendaryHeroes — either rewrites one existing reader-layer piece or drafts a new profile from a mature Case, always through Fact Lock → Narrative Packet → Structural Cut → Fidelity Readback → PR for author acceptance. Use for book/profiles, book/chapters, book/life-routes work in TrojanFighter/IndieGameLegendaryHeroes.
---

# 英雄传说编辑车道周期任务（Lane C）

仓库：`TrojanFighter/IndieGameLegendaryHeroes`。任务：每次运行交付**一篇** Lane C 候选稿 PR，等作者验收。质量标准（作者已校准）：修结构不毁文风——删减重复宣讲、恢复人物行动、调节节奏；不为可读性牺牲史实边界。

## 开工前必读（按序）

1. `AGENTS.md`（宪法：证据等级 P0/P1/S1/S2/H、禁止虚构、Lane 边界）
2. `WORKFLOW.md` + `docs/project-routing-gate.md`（车道与路由预检）
3. `book/EDITORIAL-GATE.md` + `book/EDITORIAL-REWRITE-PROTOCOL.md` + `book/TEMPORAL-VALIDITY.md`
4. `book/EDITORIAL-CODEX-HANDOFF-2026-10-09.md`（Pilot 流程与交付合同）
5. `book/OPEN-QUESTIONS.md`（选题优先级寄存器）与 `OPEN-QUESTIONS.md`（仓库根，研究优先级）
6. 已交付样例：`book/EDITORIAL-PILOT-GUNPOINT-001-20261114.md`（PR #351，作者验收过的力度标准）

## 选哪条轨（每跑一次选一条）

- **奇数 ISO 周 = 改写道**：从 `book/profiles/`、`book/chapters/`、`book/life-routes/` 选一篇做 2–3 节或全篇改写候选。选目标：协议/handoff 点名未做的（early-id-doom、chapters/06）优先，其次理论密度最高的。
- **偶数 ISO 周 = 新稿道**：从 `cases/` 里挑证据最成熟（Evidence Ledger 完整、Audit status 高、非 RESEARCHING 早期）但尚无 reader 稿的案例，走 EDITORIAL-GATE §0.5 新稿入口产出 Profile 候选。
- 跑 `git_list_prs`/搜索确认没有同人正在做同一篇；有则换下一个优先级目标。

## 改写道流程

1. 记录 baseline blob SHA 与范围（2–3 连续小节起步，不一次整篇）。
2. **Fact Lock**：列人名/时间/金额口径/团队家属外包/否定与限定词/回忆时点/UNKNOWN。
3. **Narrative Packet**：叙述对象、人物与时代、处境约束、决策节点、主导疑问、文风边界。
4. **Structural Cut**：逐段标 N/A/D/R，写保留/移位/合并/删除清单。
5. 三遍改写：Delete（优先整段删重复，不替换同义词）→ Restore Person（行动与后果可见，不虚构）→ Rhythm（不一味短句、不机械"神话→反转"）。
6. **Fidelity Readback**：逐表核 PRESERVED/NEEDS_VERIFY/REGRESSION；REGRESSION 必须改回。
7. 交付文档 `book/EDITORIAL-PILOT-<slug>-NNN-<yyyymmdd>.md`，含上述全部 + A/B（无真实读者盲测则明示 NOT TESTED），状态 `AUTHOR_REVIEW_PENDING`。

## 新稿道流程

1. 读目标 Case + Evidence Ledger 全文 + 关联 Claims/Profiles。
2. 在交付文档先留 Fact Lock + Narrative Packet（EDgate §0.5 要求，动笔前）。
3. 按人物—处境—行动—后果组织叙述；不套"神话→反转→理论总结"模板；关键事实可回指 Case/Evidence。
4. 候选稿放交付文档（同上格式），标明哪些判断是 H 级作者假说。

## 铁律（违反即作废）

- **永不改** `cases/`、`evidence/`、`claims/`、`schemas/`、lint、姊妹篇 canonical 语料；发现史实问题标 `VERIFY_IN_LANE_B`，不在 Lane C 猜。
- 不把作者分析安到人物头上（"他说"必须有出处）；不把回忆写成同期；不删 UNKNOWN/限定词；不为戏剧补场景对话。
- "可学/不可抄"类操作清单优先链接到 Life Routes，不在正文重复宣讲；免责声明同一篇最多出现一次。
- 不批量改写；一 PR 一篇；不在同一 PR 顺手改研究层。
- 数字/字数对比必须真实可复算（用统一口径统计，不写约数假精度）。

## 交付

- 分支 `devin/<ts>-<slug>`，一个 commit，PR 标题 `Lane C <track>: <target> 候选（待作者验收）`，body 含 baseline SHA、范围、Readback 结论、A/B 状态、Case/Evidence 零改动声明。
- 会话结束输出：PR URL、选的目标与理由、Readback 摘要、下一周建议目标。
