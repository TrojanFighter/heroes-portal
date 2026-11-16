# 英雄传说 · 书阁 (Indie Heroes Portal)

[IndieGameLegendaryHeroes](https://github.com/TrojanFighter/IndieGameLegendaryHeroes) 研究写作仓库的在线阅读门户：
把 book/、cases/、claims/、evidence/、sister-projects/、country-studies/、cross-industry/、translations/en/ 全部渲染成可读的静态站，另加案例地图、命题状态表、决策路由问答、图鉴。

## 结构

- `build.py` — Markdown → 静态站生成器（Python，唯一依赖 `markdown`）
- `server.py` — 本地静态服务器（clean URL → .html fallback）
- `assets/` — 生成的木刻藏书票插图（PNG 原稿 + webp 成品）
- `data/github.json` — GitHub 动态快照（`gh api` 生成）
- `public/` — 构建产物（gitignored）

## 构建

```bash
pip3 install markdown
python3 build.py                      # 输出到 public/，本地/Devin 用
SITE_BASE=/heroes-portal SITE_OUT=dist python3 build.py   # GitHub Pages 子路径构建
python3 server.py                     # 本地预览
```

## 部署

- **GitHub Pages**：`gh-pages` 分支放 `SITE_BASE=/heroes-portal` 构建产物，
  站点在 https://trojanfighter.github.io/heroes-portal/
- **Devin App**：`python3 server.py`（PORT 环境变量），deploy_devin_app 发布。
