#!/usr/bin/env python3
"""Build the 独立游戏英雄传说 reading portal from the cloned book repo."""
import json, os, re, shutil, html
import markdown

SRC = "/home/ubuntu/book-src"
OUT = "/home/ubuntu/heroes-portal/public"
DATA = "/home/ubuntu/heroes-portal/data/github.json"
REPO_URL = "https://github.com/TrojanFighter/IndieGameLegendaryHeroes"
SESSION_URL = "https://app.devin.ai/sessions/fe81bbb5c74d43ffb7d98d011a5e301b"
GEN_DATE = "2026-11-14"

RENDER_DIRS = ["book/", "cases/", "claims/"]

def site_path(repo_path):
    """repo-relative .md path -> site path (root-relative), or None."""
    p = repo_path.strip("/")
    if p == "README.md":
        return "/readme.html"
    if any(p.startswith(d) for d in RENDER_DIRS) and p.endswith(".md"):
        return "/" + p[:-3] + ".html"
    return None

def resolve_link(href, src_repo_dir):
    if href.startswith(("http://", "https://", "mailto:", "#")):
        return href
    if href.startswith("//"):
        return "https:" + href
    path, _, frag = href.partition("#")
    if not path:
        return href
    repo_path = os.path.normpath(os.path.join(src_repo_dir, path)).replace("\\", "/")
    target = site_path(repo_path)
    if target:
        return target + ("#" + frag if frag else "")
    # not rendered -> link to GitHub
    gh = f"{REPO_URL}/blob/main/{repo_path}"
    return gh + ("#" + frag if frag else "")

LINK_RE = re.compile(r'(\[!?\[[^\]]*\]\]|\[[^\]]*\]|!\[[^\]]*\])\(([^)\s]+)([^)]*)\)')
BARE_LINK_RE = re.compile(r'\]\(([^)\s]+)([^)]*)\)')

def rewrite_md(text, src_repo_dir):
    def rep(m):
        url, rest = m.group(1), m.group(2) or ""
        return f"]({resolve_link(url, src_repo_dir)}{rest})"
    return BARE_LINK_RE.sub(rep, text)

def strip_frontmatter(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            nl = text.find("\n", end + 4)
            return text[nl + 1:] if nl != -1 else ""
    return text

def first_h1(text):
    m = re.search(r'^#\s+(.+)$', text, re.M)
    if m:
        t = re.sub(r'[*`]', '', m.group(1)).strip()
        return t
    return None

def first_para(text):
    """First non-heading, non-list, non-quote, non-link-only paragraph."""
    for chunk in re.split(r'\n\s*\n', text):
        s = chunk.strip()
        if not s or s.startswith(('#', '-', '*', '>', '|', '```', '---', '<', '[')):
            continue
        s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', s)
        s = re.sub(r'[*_`]', '', s).strip()
        s = ' '.join(s.split())
        if s.startswith(('©', 'All Rights', 'English translation', '[English')):
            continue
        if len(s) > 20:
            return s[:150] + ('…' if len(s) > 150 else '')
    return ""

CSS = """
:root{--bg:#f2ecdc;--paper:#faf6ea;--ink:#2b2417;--muted:#6f6450;--faint:#9a8d76;
--border:#ddd2ba;--accent:#9e3b2d;--accent-soft:rgba(158,59,45,.08);
--teal:#1f5f5b;--radius:8px;
--serif:"Noto Serif SC","Songti SC","STSong","SimSun",serif;
--mono:"SF Mono",ui-monospace,"JetBrains Mono",Consolas,"Noto Serif SC","Songti SC",monospace}
*{box-sizing:border-box;margin:0}
html{font-size:16px}
body{background:var(--bg);color:var(--ink);font-family:var(--serif);line-height:1.75;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.nav{position:sticky;top:0;z-index:50;background:rgba(250,246,234,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--border)}
.nav-in{max-width:1120px;margin:0 auto;padding:0 20px;height:52px;display:flex;align-items:center;gap:18px;overflow-x:auto}
.brand{display:flex;align-items:center;gap:9px;font-weight:700;font-size:15px;color:var(--ink);white-space:nowrap}
.seal{width:24px;height:24px;background:var(--accent);color:#fff;border-radius:4px;display:grid;place-items:center;font-size:11px;line-height:1;font-weight:700;letter-spacing:0}
.nav a.nl{color:var(--muted);font-size:14px;white-space:nowrap;padding:4px 2px}
.nav a.nl.on,.nav a.nl:hover{color:var(--accent);text-decoration:none}
.nav .sp{flex:1}
.wrap{max-width:1120px;margin:0 auto;padding:0 20px}
.col{max-width:760px;margin:0 auto;padding:0 20px}
.hero{padding:72px 0 40px;border-bottom:1px solid var(--border)}
.hero .kicker{font-family:var(--mono);font-size:12px;letter-spacing:.18em;color:var(--accent);text-transform:uppercase}
.hero h1{font-size:clamp(34px,6vw,58px);font-weight:900;line-height:1.15;letter-spacing:.02em;margin:14px 0 10px}
.hero .en{font-size:clamp(15px,2.4vw,19px);color:var(--muted);font-style:italic}
.hero .quote{margin-top:26px;max-width:640px;font-size:17px;border-left:3px solid var(--accent);padding-left:18px;color:#453c2b}
.hero .byline{margin-top:18px;color:var(--faint);font-size:14px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:1px;background:var(--border);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;margin:34px 0 0}
.stat{background:var(--paper);padding:16px 14px}
.stat b{display:block;font-family:var(--mono);font-size:26px;font-weight:700;color:var(--accent)}
.stat span{font-size:13px;color:var(--muted)}
.sect{padding:44px 0}
.sect h2{font-size:24px;font-weight:800;margin-bottom:6px;display:flex;align-items:baseline;gap:12px}
.sect h2 small{font-size:13px;font-weight:400;color:var(--faint);font-family:var(--mono)}
.sect .lede{color:var(--muted);max-width:640px;margin-bottom:22px;font-size:15px}
.gate{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.card{background:var(--paper);border:1px solid var(--border);border-radius:var(--radius);padding:20px 22px;display:block;color:var(--ink);transition:border-color .15s,transform .15s}
a.card:hover{border-color:var(--accent);text-decoration:none;transform:translateY(-1px)}
.card .tag{font-family:var(--mono);font-size:11px;letter-spacing:.12em;color:var(--accent);text-transform:uppercase}
.card h3{font-size:19px;font-weight:700;margin:6px 0 6px}
.card p{font-size:14px;color:var(--muted);line-height:1.7}
.grid2{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}
.grid3{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
.pill{display:inline-block;font-family:var(--mono);font-size:11px;padding:1px 8px;border:1px solid var(--border);border-radius:99px;color:var(--muted);margin-left:8px}
table.atlas{width:100%;border-collapse:collapse;font-size:14px;background:var(--paper);border:1px solid var(--border)}
table.atlas th{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);text-align:left;padding:10px 12px;border-bottom:1px solid var(--border)}
table.atlas td{padding:9px 12px;border-bottom:1px solid var(--border);vertical-align:top}
table.atlas tr:last-child td{border-bottom:0}
table.atlas td.id{font-family:var(--mono);font-size:12px;white-space:nowrap}
table.atlas tr:hover td{background:var(--accent-soft)}
.panel{background:var(--paper);border:1px solid var(--border);border-radius:var(--radius);padding:24px 26px}
.why h3{font-size:17px;margin-bottom:10px}
.why p,.why li{font-size:14.5px;color:#453c2b}
.why ul{padding-left:20px;margin-top:8px}
.why li{margin-bottom:6px}
.feed{list-style:none;padding:0}
.feed li{display:flex;gap:12px;padding:9px 0;border-bottom:1px solid var(--border);font-size:14px;align-items:baseline}
.feed li:last-child{border-bottom:0}
.feed .d{font-family:var(--mono);font-size:12px;color:var(--faint);white-space:nowrap}
.feed .t{font-family:var(--mono);font-size:11px;color:var(--accent);border:1px solid var(--accent-soft);padding:0 7px;border-radius:99px;white-space:nowrap;background:var(--accent-soft)}
.feed .m{color:#453c2b;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0;flex:1}
.feed li>span:last-child{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
article.doc{padding:44px 0 30px;font-size:16.5px;line-height:1.95}
article.doc h1{font-size:32px;font-weight:900;line-height:1.3;margin-bottom:6px}
article.doc .sub{color:var(--faint);font-family:var(--mono);font-size:13px;margin-bottom:34px}
article.doc h2{font-size:24px;font-weight:800;margin:2.2em 0 .7em;padding-left:12px;border-left:3px solid var(--accent);line-height:1.4}
article.doc h3{font-size:19px;font-weight:700;margin:1.8em 0 .6em}
article.doc h4{font-size:16.5px;margin:1.5em 0 .5em}
article.doc p{margin:.9em 0}
article.doc ul,article.doc ol{padding-left:1.6em;margin:.9em 0}
article.doc li{margin-bottom:.35em}
article.doc blockquote{border-left:3px solid var(--border);padding:.2em 0 .2em 18px;margin:1.2em 0;color:#4a4130;font-style:italic}
article.doc blockquote strong{font-style:normal}
article.doc strong{color:#1f1a10}
article.doc code{font-family:var(--mono);font-size:.85em;background:rgba(43,36,23,.06);padding:2px 6px;border-radius:4px}
article.doc pre{background:#2b2417;color:#f0e9d6;padding:16px 18px;border-radius:var(--radius);overflow-x:auto;margin:1.2em 0;font-size:13px;line-height:1.6}
article.doc pre code{background:none;color:inherit;padding:0}
article.doc table{border-collapse:collapse;width:100%;margin:1.2em 0;font-size:14.5px;display:block;overflow-x:auto}
article.doc th{border-bottom:2px solid var(--ink);text-align:left;padding:8px 10px;font-weight:700;white-space:nowrap}
article.doc td{border-bottom:1px solid var(--border);padding:8px 10px;vertical-align:top}
article.doc hr{border:0;border-top:1px solid var(--border);margin:2.4em 0}
article.doc img{max-width:100%;border-radius:var(--radius)}
article.doc a{text-decoration:underline;text-decoration-color:rgba(158,59,45,.4);text-underline-offset:3px}
article.doc a:hover{color:var(--accent)}
.crumbs{font-size:13px;color:var(--faint);padding-top:26px;font-family:var(--mono)}
.crumbs a{color:var(--muted)}
.filter{width:100%;max-width:420px;font-family:var(--serif);font-size:15px;padding:9px 14px;border:1px solid var(--border);border-radius:var(--radius);background:var(--paper);color:var(--ink);margin-bottom:18px}
.filter:focus{outline:2px solid var(--accent-soft);border-color:var(--accent)}
.foot{border-top:1px solid var(--border);margin-top:20px;padding:28px 0 44px;color:var(--faint);font-size:13px}
.foot a{color:var(--muted)}
.tworow{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,.8fr);gap:16px}
.tworow>*{min-width:0}
.feed li{min-width:0}
@media(max-width:760px){.tworow{grid-template-columns:1fr}.hero{padding:48px 0 30px}}
.stat-row{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.chip{font-family:var(--mono);font-size:12px;color:var(--muted);border:1px solid var(--border);border-radius:99px;padding:2px 10px}
.chip b{color:var(--ink);font-weight:600}
.status{font-family:var(--mono);font-size:11px;letter-spacing:.06em;color:var(--teal);border:1px solid rgba(31,95,91,.25);border-radius:99px;padding:1px 9px;background:rgba(31,95,91,.06)}
"""

TPL = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 独立游戏英雄传说</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='%239e3b2d'/><text x='16' y='22' font-size='17' text-anchor='middle' fill='white' font-family='serif'>传</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
<nav class="nav"><div class="nav-in">
<a class="brand" href="/"><span class="seal">传</span>英雄传说 · 书阁</a>
<a class="nl{n_start}" href="/book/START-HERE.html">从这儿读</a>
<a class="nl{n_ch}" href="/chapters.html">章节</a>
<a class="nl{n_pf}" href="/profiles.html">人物</a>
<a class="nl{n_rt}" href="/book/DECISION-ROUTER.html">决策路由</a>
<a class="nl{n_at}" href="/atlas.html">案例地图</a>
<a class="nl{n_cl}" href="/claims.html">命题</a>
<a class="nl{n_no}" href="/notes.html">笔记</a>
<span class="sp"></span>
<a class="nl" href="https://github.com/TrojanFighter/IndieGameLegendaryHeroes" target="_blank" rel="noopener">GitHub ↗</a>
</div></nav>
{body}
<footer class="foot"><div class="wrap">
《独立游戏英雄传说》 · 洪荒行者 · 内容取自 <a href="https://github.com/TrojanFighter/IndieGameLegendaryHeroes">IndieGameLegendaryHeroes</a> 仓库（{date} 快照） · <a href="{sess}">向 Devin 提修改需求</a>
</div></footer>
</body></html>"""

def page(title, body, nav=""):
    keys = {k: "" for k in ["n_start","n_ch","n_pf","n_rt","n_at","n_cl","n_no"]}
    if nav:
        keys[nav] = ' class="on"'
    t = TPL.replace("{title}", html.escape(title)).replace("{css}", CSS)
    t = t.replace("{body}", body).replace("{date}", GEN_DATE).replace("{sess}", SESSION_URL)
    for k, v in keys.items():
        t = t.replace("{" + k + "}", v)
    return t

MDX = markdown.Markdown(extensions=["extra", "toc", "sane_lists", "smarty"])

def render_doc(repo_path):
    """Render one repo md file; return (title, out_rel_path)."""
    raw = open(os.path.join(SRC, repo_path), encoding="utf-8").read()
    body = strip_frontmatter(raw)
    title = first_h1(body) or os.path.basename(repo_path)[:-3]
    src_dir = os.path.dirname(repo_path)
    body = rewrite_md(body, src_dir)
    MDX.reset()
    inner = MDX.convert(body)
    crumbs = '<div class="crumbs"><a href="/">书阁</a> / ' + html.escape(repo_path) + '</div>'
    art = f'<article class="doc"><div class="col">{inner}{crumbs}</div></article>'
    nav = {"book/chapters/": "n_ch", "book/profiles/": "n_pf", "book/research-notes/": "n_no",
           "book/life-routes/": "n_rt", "cases/": "n_at", "claims/": "n_cl"}.get(
               next((p for p in ("book/chapters/","book/profiles/","book/research-notes/","book/life-routes/","cases/","claims/") if repo_path.startswith(p)), ""), "n_start" if repo_path.startswith("book/") else "")
    return title, art, nav

def write(rel, content):
    p = os.path.join(OUT, rel.lstrip("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(content)

def collect(pattern_dir):
    files = []
    d = os.path.join(SRC, pattern_dir)
    for root, _, names in os.walk(d):
        for n in sorted(names):
            if n.endswith(".md"):
                files.append(os.path.relpath(os.path.join(root, n), SRC))
    return files

def meta(repo_path):
    raw = strip_frontmatter(open(os.path.join(SRC, repo_path), encoding="utf-8").read())
    return first_h1(raw) or repo_path, first_para(raw)

def claim_status(repo_path):
    raw = open(os.path.join(SRC, repo_path), encoding="utf-8").read()
    m = re.search(r'Status:\s*([A-Z]+)', raw)
    return m.group(1) if m else ""

def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    docs = collect("book") + collect("cases") + collect("claims") + ["README.md"]
    doc_titles = {}
    for rp in sorted(docs):
        title, art, nav = render_doc(rp)
        doc_titles[rp] = title
        write(site_path(rp), page(title, art, nav))
    print("rendered docs:", len(docs))

    gh = json.load(open(DATA, encoding="utf-8"))

    # ---- index ----
    cases = [f for f in docs if re.match(r"cases/CASE-", f)]
    claims = [f for f in docs if f.startswith("claims/C") and "README" not in f]
    chaps = sorted(f for f in docs if f.startswith("book/chapters/") and "README" not in f)
    profs = sorted(f for f in docs if f.startswith("book/profiles/") and "README" not in f)
    routes = sorted(f for f in docs if f.startswith("book/life-routes/") and "README" not in f)
    notes = [f for f in docs if f.startswith("book/research-notes/") and "README" not in f]

    stats = [
        (str(len(cases)), "编号研究案例"),
        (str(len(profs)), "人物传记"),
        (str(len(chaps)), "跨人物章节"),
        ("15", "跨案例命题"),
        (str(len(notes)), "研究笔记"),
        (str(gh["user"]["public_repos"]), "公开仓库"),
    ]
    stat_html = "".join(f'<div class="stat"><b>{n}</b><span>{s}</span></div>' for n, s in stats)

    chap_cards = ""
    for f in chaps:
        t, teaser = meta(f)
        num = os.path.basename(f)[:2]
        chap_cards += f'''<a class="card" href="{site_path(f)}"><span class="tag">第 {num} 章</span><h3>{html.escape(t)}</h3><p>{html.escape(teaser)}</p></a>'''

    feed_items = ""
    icon = {"push": "PUSH", "pr-opened": "PR", "pr-merged": "MERGED", "pr-closed": "PR",
            "star": "★", "fork": "FORK"}
    for e in gh["feed"][:14]:
        d = e["date"][:10]
        ty = icon.get(e["type"], e["type"].upper()[:6])
        repo = html.escape(e["repo"])
        if e["text"]:
            txt = html.escape(e["text"]) + f' <span style="color:var(--faint)">· {repo}</span>'
        else:
            txt = repo
        feed_items += f'<li><span class="d">{d}</span><span class="t">{ty}</span><span class="m">{txt}</span></li>'

    lang_chips = "".join(f'<span class="chip"><b>{l}</b> ×{c}</span>' for l, c in gh["lang_own"][:6])

    recent_work = [
        ("IndieGameLegendaryHeroes", "11-12", "本书仓库 · 63 案例研究后台", False),
        ("ReverseEngineeringProject1", "11-12", "游戏内容组织与生成机制研究", True),
        ("KungfuWarlordPunk-DesignDocuments", "11-09", "功夫武侠朋克 · 设计文档", True),
        ("DragonFly-Site", "11-08", "DragonFly 站点", True),
        ("KungfuWarlordPunk-Art1", "11-05", "功夫武侠朋克 · 美术", True),
        ("BladeInquisitor-Site / Prototype1", "10-29", "刀锋审判官 · 站点与 LÖVE 原型", True),
    ]
    rw_items = []
    for n, d, desc, pv in recent_work:
        pill = ' <span class="pill">私有</span>' if pv else ''
        rw_items.append(f'<li><span class="d">2026-{d}</span><span class="m">{html.escape(n)}{pill}</span><span style="color:var(--faint);font-size:12px">{html.escape(desc)}</span></li>')
    rw = "".join(rw_items)

    body = f'''
<header class="hero"><div class="wrap">
<div class="kicker">Indie Game Legendary Heroes · 在线书阁</div>
<h1>独立游戏英雄传说</h1>
<div class="en">那些本来"做不起游戏"的人，究竟是怎样把游戏做出来的</div>
<blockquote class="quote">不包装天才神话，不把"坚持"和"运气"当答案——追踪的是开工前会什么、靠什么活下来、失败如何变成下一作的资产、以及什么能复制、什么不能。</blockquote>
<div class="byline">作者 / 主创：洪荒行者 · Sparky（TrojanFighter） · Wunderwaffe Development</div>
<div class="stats">{stat_html}</div>
</div></header>

<section class="sect"><div class="wrap">
<h2>两个入口<small>读人生，或者查证据</small></h2>
<p class="lede">第一次来只想读人和故事，走左边；想核每句话的证据强度，走右边。</p>
<div class="gate">
<a class="card" href="/book/START-HERE.html"><span class="tag">读者入口</span><h3>第一次来，先从这里读 →</h3><p>按现实问题组织：不知道该做什么、该不该辞职、没钱怎么办、失败还有没有意义。七篇跨人物章节 + 十四篇人物传记。</p></a>
<a class="card" href="/atlas.html"><span class="tag">研究后台</span><h3>案例地图与证据台账 →</h3><p>63 个编号 Case 档案、15 个可证伪命题、证据等级 P0/P1/S1/S2/H、反例与禁止外推。每句话都能追来源。</p></a>
</div>
</div></section>

<section class="sect" style="padding-top:8px"><div class="wrap">
<h2>书稿章节<small>跨人物成品叙事</small></h2>
<div class="grid3">{chap_cards}</div>
<div style="margin-top:14px"><a href="/profiles.html">十四篇人物传记 →</a> · <a href="/book/life-routes/README.html">生命风险路线 →</a> · <a href="/book/READER-ARCHETYPES.html">按主创能力进入 →</a></div>
</div></section>

<section class="sect" style="padding-top:8px"><div class="wrap">
<h2>为什么是这个 App<small>根据你的公开活动</small></h2>
<div class="panel why">
<h3>判断依据</h3>
<p>根据 GitHub 上的真实活动，你的主线已经不只是"写代码"：</p>
<ul>
<li><b>当前主轴是这本书。</b> IndieGameLegendaryHeroes 是你 10 月以来几乎天天在推进的项目——63 个案例档案、7 篇章节、14 篇人物稿，但它现在还只躺在 Markdown 仓库里，没有一个"能读"的形态。</li>
<li><b>你是游戏开发出身。</b> 2015–2019 年的 Unity/C# 原型、NYU Game Center 关卡设计、游戏物理与编程模式笔记——这本书研究的就是你自己这个群体。</li>
<li><b>你在并行推进多个原型。</b> BladeInquisitor、KungfuWarlordPunk、DragonFly 等私有仓库近两周仍在更新，同时大量试用 AI agent 工作流（inkos、codex skills、DeepSeek-Reasonix）。</li>
<li><b>所以最贴切的 App 是：</b>把《独立游戏英雄传说》变成一座真正能给人看的"书阁"——读者走叙事层，研究者走证据层，这个页面就是答案本身。</li>
</ul>
<div class="stat-row" style="margin-top:14px">{lang_chips}</div>
</div>
</div></section>

<section class="sect" style="padding-top:0"><div class="wrap">
<div class="tworow">
<div class="panel"><h3 style="font-size:16px;margin-bottom:8px">近一个月的活跃仓库</h3><ul class="feed">{rw}</ul></div>
<div class="panel"><h3 style="font-size:16px;margin-bottom:8px">GitHub 公开动态</h3><ul class="feed">{feed_items}</ul></div>
</div>
</div></section>
'''
    write("/index.html", page("首页", body))
    print("index done")

    # ---- chapters index ----
    cards = ""
    for f in chaps:
        t, teaser = meta(f)
        num = os.path.basename(f)[:2]
        cards += f'<a class="card" href="{site_path(f)}"><span class="tag">第 {num} 章</span><h3>{html.escape(t)}</h3><p>{html.escape(teaser)}</p></a>'
    body = f'<section class="sect"><div class="wrap"><h2>跨人物章节<small>{len(chaps)} 篇样稿</small></h2><p class="lede">把多个人物放进同一个现实问题里读：目标、时间、失败、技术、市场、团队、以及第一次成功之后。</p><div class="grid2">{cards}</div></div></section>'
    write("/chapters.html", page("章节", body, "n_ch"))

    # ---- profiles index ----
    cards = ""
    for f in profs:
        t, teaser = meta(f)
        cards += f'<a class="card" href="{site_path(f)}"><h3>{html.escape(t)}</h3><p>{html.escape(teaser)}</p></a>'
    body = f'<section class="sect"><div class="wrap"><h2>人物传记<small>{len(profs)} 篇</small></h2><p class="lede">制作经历与职业选择：从插画师与 AAA 程序员的合伙，到上班养游戏的个人作者。</p><div class="grid2">{cards}</div></div></section>'
    write("/profiles.html", page("人物传记", body, "n_pf"))

    # ---- atlas (case table parsed from README) ----
    readme = open(os.path.join(SRC, "README.md"), encoding="utf-8").read()
    rows = re.findall(r'\|\s*\[([^\]]+)\]\((cases/[^)]+)\)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|', readme)
    trs = ""
    n_cases = 0
    for cid, link, subj, blurb in rows:
        if not re.match(r"CASE-\d+", cid):
            continue
        n_cases += 1
        subj = re.sub(r'[*`]', '', subj).strip()
        blurb = re.sub(r'`', '', blurb).strip()
        trs += f'<tr><td class="id"><a href="{site_path(link)}">{cid}</a></td><td>{html.escape(subj)}</td><td>{html.escape(blurb)}</td></tr>'
    body = f'''<section class="sect"><div class="wrap">
<h2>案例地图<small>{n_cases} 个编号 Case</small></h2>
<p class="lede">Case ID 用于审计，不代表证据成熟度或推荐阅读顺序。带"待核"标记的对象尚未全部核实生产史与独立资格。</p>
<input class="filter" id="f" placeholder="筛选案例：编号 / 游戏名 / 关键词…" oninput="q(this.value)">
<table class="atlas" id="t"><tr><th>Case</th><th>对象</th><th>它主要让我们看见什么</th></tr>{trs}</table>
</div></section>
<script>function q(v){{v=v.toLowerCase();document.querySelectorAll('#t tr').forEach((r,i)=>{{if(i==0)return;r.style.display=r.innerText.toLowerCase().includes(v)?'':'none'}})}}</script>'''
    write("/atlas.html", page("案例地图", body, "n_at"))

    # ---- claims index: 15 rows from claims/README.md + full docs where present ----
    creadme = open(os.path.join(SRC, "claims/README.md"), encoding="utf-8").read()
    crows = re.findall(r'\|\s*(C\d{3})\s*\|\s*(.*?)\s*\|\s*([A-Z]+)\s*\|', creadme)
    claim_file = {}
    for f in claims:
        m = re.match(r"claims/(C\d{3})", f)
        if m:
            claim_file[m.group(1)] = f
    trs = ""
    for cid, stmt, st in crows:
        link = claim_file.get(cid)
        cell = f'<a href="{site_path(link)}">{cid}</a>' if link else cid
        trs += f'<tr><td class="id">{cell}</td><td><span class="status">{st}</span></td><td>{html.escape(stmt)}</td></tr>'
    extra = f'<div style="margin-top:14px"><a href="/claims/CROSS-CASE-READINGS.html">跨案例综合、反例与边界 →</a></div>'
    body = f'''<section class="sect"><div class="wrap">
<h2>跨案例命题<small>{len(crows)} 个</small></h2>
<p class="lede">每个命题都可被支持、削弱或证伪。SUPPORTED 只表示已有多源 / 跨案例支持，仍不等于普遍规律或因果定论；C013–C015 有完整档案可点进。</p>
<table class="atlas"><tr><th>Claim</th><th>状态</th><th>暂定命题</th></tr>{trs}</table>{extra}
</div></section>'''
    write("/claims.html", page("跨案例命题", body, "n_cl"))

    # ---- notes index ----
    items = ""
    for f in sorted(notes):
        t, _ = meta(f)
        items += f'<li><a href="{site_path(f)}">{html.escape(t)}</a></li>'
    body = f'''<section class="sect"><div class="wrap">
<h2>研究笔记<small>{len(notes)} 篇</small></h2>
<p class="lede">过程性研究产出：审计、对照矩阵、叙事试验、清理记录——支撑章节与命题的底稿。</p>
<input class="filter" id="f" placeholder="筛选笔记…" oninput="q(this.value)">
<ul id="t" style="columns:2;column-gap:40px;font-size:14.5px;line-height:2">{items}</ul>
</div></section>
<script>function q(v){{v=v.toLowerCase();document.querySelectorAll('#t li').forEach(r=>{{r.style.display=r.innerText.toLowerCase().includes(v)?'':'none'}})}}</script>'''
    write("/notes.html", page("研究笔记", body, "n_no"))

    print("done ->", OUT)

if __name__ == "__main__":
    main()
