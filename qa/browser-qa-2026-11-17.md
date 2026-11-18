# 英雄传说书阁 · GH Pages 浏览器验收报告

- 站点：https://trojanfighter.github.io/heroes-portal/
- 检查方法：game-site-production skill 的 browser-qa 清单（按用户给定的路由×视口矩阵执行，用真实 Chrome + DevTools console 实测，非脚本模拟）
- 日期：2026-11-15（会话内实测）

## 总体结论

**1 个高优先级缺陷**：`/router.html` 决策问答的推荐结果链接全部为**未加 `/heroes-portal/` 前缀的根相对路径**（如 `/cases/CASE-045-rimworld.html`），在 GitHub Pages 子路径部署下**全部 404**。其余检查项全部通过。

修复建议：build.py 生成 router.html 时，给 JS `R` 映射里的 `"h"` 字段同样加上 base 前缀（HTML 里的静态 href 都已正确加前缀，只有这一处 JS 数据漏了）。

---

## 路由 × 视口矩阵（HTTP 200 / h1 / 横向溢出 / 控制台）

| 路由 | 200 | h1 | 溢出@1440 | 溢出@375 | 溢出@320 | 控制台 |
|---|---|---|---|---|---|---|
| `/` 首页 | ✅ | ✅ | 无 | 372/387 | 305/320 | 干净 |
| `/chapters.html` | ✅ | ✅ | 无 | — | — | 干净 |
| `/book/chapters/01-…html` | ✅ | ✅ | 无 | 372/387 | — | 干净 |
| `/profiles.html` | ✅ | ✅ | 无 | — | — | 干净 |
| `/book/profiles/ftl.html` | ✅ | ✅ | 无 | — | — | 干净 |
| `/atlas.html` | ✅ | ✅ | 无 | 372/387 | 305/320 | 干净 |
| `/claims.html` | ✅ | ✅ | 无 | 372/387 | — | 干净 |
| `/router.html` | ✅ | ✅ | 无 | — | 305/320 | 干净 |
| `/gallery.html` | ✅ | ✅ | 无 | 372/387 | 305/320 | 干净 |
| `/sections.html` | ✅ | ✅ | 无 | — | 305/320 | 干净 |
| `/notes.html` | ✅ | ✅ | 无 | 372/387 | — | 干净 |
| `/en/` 英文落地页 | ✅ | ✅ | 无 | 372/387 | — | 干净 |
| `/cases/CASE-001-ftl.html`（含表格正文页） | ✅ | ✅ | 无 | — | 305/320 | 干净 |

（scrollWidth/innerWidth 数值为 DevTools console 实测；< = 无横向溢出。全站 462 条内链全部 200。）

## 交互实测

| 项目 | 结果 |
|---|---|
| 决策问答 3 步 | 选项可选、结果面板正常渲染；**但推荐链接 404（见缺陷）** |
| atlas 筛选 | ✅ 输入 "stardew" 63 行过滤到 CASE-004；台账链接可开 |
| 暗色模式 | ✅ ◐ 切换、刷新后保持（localStorage），明暗两态可读 |
| 中英切换 | ✅ CASE-001 "English translation →" → EN 页 →"阅读中文原文 →" 往返正常 |
| gallery 懒加载 | ✅ 滚动触发后 ~20 张 webp 全部解码，无裂图 |
| 导航横滑条 | ✅ 320px 下 `.nav-in` scrollWidth 888 > clientWidth 372，可滑动，末项（图鉴/◐/GitHub）可达 |

## 双语诚实核对

英文入口不误导：`/en/` 落地页明确写 "Most of the book is in Chinese; English translations are growing in translations/en — CASE-001 (FTL) is fully translated"，三个入口卡都标 "(Chinese)"，并给出 "中文版 →" 回链。覆盖面如实：完整英文内容目前只有 CASE-001 一篇译稿 + 落地页本身。

## 通过 / 失败 / 未做

- **通过**：全部路由 200 + h1；所有视口无横向溢出（含刚修的 atlas）；图片解码；控制台无错；导航可达；atlas 筛选；暗色持久；中英往返；英文覆盖诚实；462 条内链全通。
- **失败**：router 结果链接 404（前缀缺失）—— 唯一阻塞项。
- **未做**：`/sections.html` 组内逐条链接点击（抽查了 CASE-004 台账，同类链接同源生成，curl 全扫已证 200）；多语言切换在 `/en/` 之外页面的逐项验证（只有 CASE-001 有译稿，已验）；iOS Safari / 真机触摸滑动（本机无 Safari，导航滑动用 scrollLeft 验证）。

## 附注

- 旧的 localhost:8000/8001 服务已不在本次范围；本次只对线上 GH Pages 版本验收。
- 测试期间发现的同类风险已确认隔离：静态 HTML href 全部带前缀，仅 router 的 JS 数据缺前缀。
