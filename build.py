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

RENDER_DIRS = ["book/", "cases/", "claims/", "evidence/", "sister-projects/",
               "country-studies/", "cross-industry/", "translations/en/"]

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
--ink2:#453c2b;--strong:#1f1a10;--code-bg:rgba(43,36,23,.06);--nav-bg:rgba(250,246,234,.92);
--serif:"Noto Serif SC","Songti SC","STSong","SimSun",serif;
--mono:"SF Mono",ui-monospace,"JetBrains Mono",Consolas,"Noto Serif SC","Songti SC",monospace}
[data-theme="dark"]{--bg:#14110c;--paper:#1e1a13;--ink:#e6ddc8;--ink2:#d3c8ae;--strong:#f2ead6;
--muted:#a3977f;--faint:#7d7260;--border:#3a3220;--accent:#d4674c;--accent-soft:rgba(212,103,76,.14);
--teal:#5ea8a0;--code-bg:rgba(230,221,200,.08);--nav-bg:rgba(20,17,12,.9)}
*{box-sizing:border-box;margin:0}
html{font-size:16px}
body{background:var(--bg);color:var(--ink);font-family:var(--serif);line-height:1.75;-webkit-font-smoothing:antialiased;
background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='140' height='140' filter='url(%23n)' opacity='0.045'/%3E%3C/svg%3E")}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.nav{position:sticky;top:0;z-index:50;background:var(--nav-bg);backdrop-filter:blur(8px);border-bottom:1px solid var(--border)}
.nav-in{max-width:1120px;margin:0 auto;padding:0 20px;height:52px;display:flex;align-items:center;gap:18px;overflow-x:auto}
.brand{display:flex;align-items:center;gap:9px;font-weight:700;font-size:15px;color:var(--ink);white-space:nowrap}
.seal{width:24px;height:24px;background:var(--accent);color:#fff;border-radius:4px;display:grid;place-items:center;font-size:11px;line-height:1;font-weight:700;letter-spacing:0}
.nav a.nl{color:var(--muted);font-size:14px;white-space:nowrap;padding:4px 2px}
.nav a.nl.on,.nav a.nl:hover{color:var(--accent);text-decoration:none}
.nav a.nl.on{box-shadow:inset 0 -2px 0 var(--accent)}
.nav .sp{flex:1}
.wrap{max-width:1120px;margin:0 auto;padding:0 20px}
.col{max-width:760px;margin:0 auto;padding:0 20px}
.hero{padding:72px 0 40px;border-bottom:1px solid var(--border)}
.hero .kicker{font-family:var(--mono);font-size:12px;letter-spacing:.18em;color:var(--accent);text-transform:uppercase}
.hero h1{font-size:clamp(34px,6vw,58px);font-weight:900;line-height:1.15;letter-spacing:.02em;margin:14px 0 10px}
.hero .en{font-size:clamp(15px,2.4vw,19px);color:var(--muted);font-style:italic}
.hero .quote{margin-top:26px;max-width:640px;font-size:17px;border-left:3px solid var(--accent);padding-left:18px;color:var(--ink2)}
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
.card{position:relative;overflow:hidden;background:var(--paper);border:1px solid var(--border);border-radius:var(--radius);padding:20px 22px;display:block;color:var(--ink);transition:border-color .15s,transform .15s}
.card::before{content:"";position:absolute;left:0;top:0;right:0;height:3px;background:var(--accent);transform:scaleX(0);transform-origin:left;transition:transform .25s}
.card:hover::before{transform:scaleX(1)}
.bignum{position:absolute;right:12px;top:0;font-size:56px;font-weight:900;color:var(--accent);opacity:.09;pointer-events:none;line-height:1}
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
table.atlas tr:nth-child(even) td{background:var(--code-bg)}
table.atlas tr:hover td{background:var(--accent-soft)}
.panel{background:var(--paper);border:1px solid var(--border);border-radius:var(--radius);padding:24px 26px}
.why h3{font-size:17px;margin-bottom:10px}
.why p,.why li{font-size:14.5px;color:var(--ink2)}
.why ul{padding-left:20px;margin-top:8px}
.why li{margin-bottom:6px}
.feed{list-style:none;padding:0}
.feed li{display:flex;gap:12px;padding:9px 0;border-bottom:1px solid var(--border);font-size:14px;align-items:baseline}
.feed li:last-child{border-bottom:0}
.feed .d{font-family:var(--mono);font-size:12px;color:var(--faint);white-space:nowrap}
.feed .t{font-family:var(--mono);font-size:11px;color:var(--accent);border:1px solid var(--accent-soft);padding:0 7px;border-radius:99px;white-space:nowrap;background:var(--accent-soft)}
.feed .m{color:var(--ink2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0;flex:1}
.feed li>span:last-child{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
article.doc{padding:44px 0 30px;font-size:16.5px;line-height:1.95}
article.doc h1{font-size:32px;font-weight:900;line-height:1.3;margin-bottom:6px;border-bottom:1px solid var(--border);padding-bottom:14px}
article.doc.lit .dc::first-letter{float:left;font-size:3.1em;line-height:.88;font-weight:900;color:var(--accent);padding:6px 10px 0 0}
article.doc .sub{color:var(--faint);font-family:var(--mono);font-size:13px;margin-bottom:34px}
article.doc h2{font-size:24px;font-weight:800;margin:2.2em 0 .7em;padding-left:12px;border-left:3px solid var(--accent);line-height:1.4}
article.doc h3{font-size:19px;font-weight:700;margin:1.8em 0 .6em}
article.doc h4{font-size:16.5px;margin:1.5em 0 .5em}
article.doc p{margin:.9em 0}
article.doc ul,article.doc ol{padding-left:1.6em;margin:.9em 0}
article.doc li{margin-bottom:.35em}
article.doc blockquote{border-left:3px solid var(--border);padding:.2em 0 .2em 18px;margin:1.2em 0;color:var(--ink2);font-style:italic}
article.doc blockquote strong{font-style:normal}
article.doc strong{color:var(--strong)}
article.doc code{font-family:var(--mono);font-size:.85em;background:var(--code-bg);padding:2px 6px;border-radius:4px}
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
.status.st-contested{color:#a8622a;border-color:rgba(168,98,42,.35);background:rgba(168,98,42,.08)}
.status.st-weak,.status.st-unverified{color:var(--faint);border-color:var(--border);background:transparent}
.status.st-refuted{color:var(--accent);border-color:rgba(158,59,45,.4);background:var(--accent-soft)}
.stamp{display:inline-grid;place-items:center;width:44px;height:44px;background:var(--accent);color:#fff;font-size:24px;font-weight:900;border-radius:6px;transform:rotate(-8deg);margin-left:16px;vertical-align:middle;box-shadow:0 2px 6px rgba(43,36,23,.3)}
.tbtn{font-family:var(--mono);font-size:12px;color:var(--muted);background:none;border:1px solid var(--border);border-radius:99px;padding:3px 10px;cursor:pointer;white-space:nowrap}
.tbtn:hover{color:var(--accent);border-color:var(--accent)}
#prog{position:fixed;top:52px;left:0;right:0;height:2px;z-index:60;pointer-events:none}
#prog i{display:block;height:100%;width:0;background:var(--accent)}
.lang-sw{font-family:var(--mono);font-size:12px;margin-bottom:22px}
.lang-sw a{color:var(--teal);border:1px solid var(--teal);border-radius:99px;padding:2px 11px;text-decoration:none;opacity:.85}
.toc{position:fixed;top:96px;right:22px;width:186px;max-height:calc(100vh - 140px);overflow:auto;font-size:12.5px;line-height:1.55;display:none;border-left:1px solid var(--border);padding-left:14px;z-index:40}
.toc .toc-t{font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;color:var(--faint);margin-bottom:8px}
.toc a{display:block;color:var(--muted);padding:2.5px 0;text-decoration:none}
.toc a.t3{padding-left:12px;font-size:12px}
.toc a.on,.toc a:hover{color:var(--accent)}
@media(min-width:1320px){.toc{display:block}}
.qz-step{background:var(--paper);border:1px solid var(--border);border-radius:var(--radius);padding:20px 22px;margin-bottom:16px}
.qz-step h3{font-size:17px;margin-bottom:3px}
.qz-step .qd{font-size:13.5px;color:var(--muted);margin-bottom:12px}
.qz-opt{display:block;width:100%;text-align:left;font-family:var(--serif);font-size:14.5px;color:var(--ink);background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:10px 14px;margin-bottom:8px;cursor:pointer}
.qz-opt:hover{border-color:var(--accent)}
.qz-opt.sel{border-color:var(--accent);background:var(--accent-soft);box-shadow:inset 3px 0 0 var(--accent)}
.qz-opt b{display:block;font-weight:700}
.qz-opt span{font-size:13px;color:var(--muted)}
.qz-res{background:var(--paper);border:1px solid var(--accent);border-radius:var(--radius);padding:22px 24px;display:none;margin-top:4px}
.qz-res h3{font-size:19px}
.qz-res .qn{font-size:13px;color:var(--muted)}
.qz-res h4{font-family:var(--mono);font-size:11.5px;letter-spacing:.1em;color:var(--accent);margin:18px 0 6px;text-transform:uppercase}
.qz-res ul{padding-left:20px;font-size:14.5px}
.qz-res li{margin-bottom:4px}
.qz-note{font-size:13.5px;color:var(--ink2);border-left:3px solid var(--border);padding-left:12px;margin:8px 0}
.qz-warn{font-size:13px;color:var(--muted);border-top:1px dashed var(--border);margin-top:16px;padding-top:12px}
.qz-reset{font-family:var(--mono);font-size:12px;color:var(--faint);background:none;border:0;cursor:pointer;text-decoration:underline;margin-left:10px;padding:0}
.sect-grp{margin-bottom:30px}
.sect-grp h3{font-size:18px;margin-bottom:4px}
.sect-grp .gd{font-size:13px;color:var(--muted);margin-bottom:10px}
.sect-grp ul{list-style:none;padding:0;font-size:14px;line-height:2}
.heroart{display:block;width:100%;max-width:860px;margin:32px auto 0;border:1px solid var(--border);border-radius:var(--radius);box-shadow:0 2px 16px rgba(43,36,23,.14)}
"""

TPL = """<!doctype html>
<html lang="{lang}">
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
<a class="nl{n_rt}" href="/router.html">决策路由</a>
<a class="nl{n_at}" href="/atlas.html">案例地图</a>
<a class="nl{n_cl}" href="/claims.html">命题</a>
<a class="nl{n_no}" href="/notes.html">笔记</a>
<a class="nl{n_sec}" href="/sections.html">分区</a>
<span class="sp"></span>
<button class="tbtn" id="thm" title="切换明暗主题">◐</button>
<a class="nl" href="https://github.com/TrojanFighter/IndieGameLegendaryHeroes" target="_blank" rel="noopener">GitHub ↗</a>
</div></nav>
<div id="prog"><i id="prog-i"></i></div>
{body}
<footer class="foot"><div class="wrap">
《独立游戏英雄传说》 · 洪荒行者 · 内容取自 <a href="https://github.com/TrojanFighter/IndieGameLegendaryHeroes">IndieGameLegendaryHeroes</a> 仓库（{date} 快照） · <a href="{sess}">向 Devin 提修改需求</a>
</div></footer>
<script>
(function(){
var d=document.documentElement;
var s=localStorage.getItem('theme');
if(s){d.dataset.theme=s}else if(matchMedia('(prefers-color-scheme: dark)').matches){d.dataset.theme='dark'}
var b=document.getElementById('thm'),pi=document.getElementById('prog-i');
function upd(){b.textContent=d.dataset.theme==='dark'?'☾ 明':'◐ 暗'}upd();
b.onclick=function(){var t=d.dataset.theme==='dark'?'light':'dark';d.dataset.theme=t;localStorage.setItem('theme',t);upd()};
addEventListener('scroll',function(){var h=document.documentElement;var m=h.scrollHeight-h.clientHeight;pi.style.width=(m>0?h.scrollTop/m*100:0)+'%'},{passive:true});
var links=document.querySelectorAll('.toc a');
if(links.length&&'IntersectionObserver' in window){
var map={};links.forEach(function(a){map[a.getAttribute('href').slice(1)]=a});
var io=new IntersectionObserver(function(es){es.forEach(function(e){var a=map[e.target.id];if(a&&e.isIntersecting){links.forEach(function(x){x.classList.remove('on')});a.classList.add('on')}})},{rootMargin:'-8% 0px -82% 0px'});
document.querySelectorAll('article.doc h2[id],article.doc h3[id]').forEach(function(h){io.observe(h)});
}})();
</script>
</body></html>"""

def page(title, body, nav="", lang="zh-CN"):
    keys = {k: "" for k in ["n_start","n_ch","n_pf","n_rt","n_at","n_cl","n_no","n_sec"]}
    if nav:
        keys[nav] = ' class="on"'
    t = TPL.replace("{title}", html.escape(title)).replace("{css}", CSS)
    t = t.replace("{lang}", lang)
    t = t.replace("{body}", body).replace("{date}", GEN_DATE).replace("{sess}", SESSION_URL)
    for k, v in keys.items():
        t = t.replace("{" + k + "}", v)
    return t

MDX = markdown.Markdown(extensions=["extra", "toc", "sane_lists", "smarty"])

def render_doc(repo_path, docset):
    """Render one repo md file; return (title, article_html, nav_key, lang)."""
    raw = open(os.path.join(SRC, repo_path), encoding="utf-8").read()
    body = strip_frontmatter(raw)
    title = first_h1(body) or os.path.basename(repo_path)[:-3]
    src_dir = os.path.dirname(repo_path)
    body = rewrite_md(body, src_dir)
    MDX.reset()
    inner = MDX.convert(body)
    # drop-cap marker: first real paragraph (skip ©/rights lines)
    inner = re.sub(r'<p>(?!©)', '<p class="dc">', inner, count=1)
    crumbs = '<div class="crumbs"><a href="/">书阁</a> / ' + html.escape(repo_path) + '</div>'
    # bilingual switch when a rendered counterpart exists
    sw = ""
    if repo_path.startswith("translations/en/"):
        cp = repo_path[len("translations/en/"):]
        if cp in docset:
            sw = f'<div class="lang-sw"><a href="{site_path(cp)}">阅读中文原文 →</a></div>'
    else:
        cp = "translations/en/" + repo_path
        if cp in docset:
            sw = f'<div class="lang-sw"><a href="{site_path(cp)}">English translation →</a></div>'
    # per-page TOC sidebar from h2/h3 (wide screens only)
    toc = ""
    heads = re.findall(r'<h([23])[^>]*id="([^"]+)"[^>]*>(.*?)</h\1>', inner)
    if len(heads) >= 3:
        items = ""
        for lv, hid, txt in heads:
            t = re.sub(r"<[^>]+>", "", txt).strip()
            if t:
                items += f'<a href="#{hid}" class="t{lv}">{html.escape(t)}</a>'
        if items:
            toc = f'<aside class="toc"><div class="toc-t">本页目录</div>{items}</aside>'
    lit = any(repo_path.startswith(p) for p in ("book/chapters/", "book/profiles/", "book/life-routes/"))
    art = toc + f'<article class="doc{" lit" if lit else ""}"><div class="col">{sw}{inner}{crumbs}</div></article>'
    prefixes = ("book/chapters/","book/profiles/","book/research-notes/","book/life-routes/",
                "cases/","claims/","evidence/","sister-projects/","country-studies/",
                "cross-industry/","translations/en/")
    nav_map = {"book/chapters/":"n_ch","book/profiles/":"n_pf","book/research-notes/":"n_no",
               "book/life-routes/":"n_rt","cases/":"n_at","claims/":"n_cl",
               "evidence/":"n_sec","sister-projects/":"n_sec","country-studies/":"n_sec",
               "cross-industry/":"n_sec","translations/en/":"n_sec"}
    nav = nav_map.get(next((p for p in prefixes if repo_path.startswith(p)), ""),
                      "n_start" if repo_path.startswith("book/") else "")
    lang = "en" if repo_path.startswith("translations/en/") else "zh-CN"
    return title, art, nav, lang

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
    # copy generated art assets (webp only; PNG masters stay in assets/)
    os.makedirs(os.path.join(OUT, "assets"))
    for n in os.listdir("/home/ubuntu/heroes-portal/assets"):
        if n.endswith(".webp"):
            shutil.copy(os.path.join("/home/ubuntu/heroes-portal/assets", n), os.path.join(OUT, "assets", n))

    docs = (collect("book") + collect("cases") + collect("claims") + collect("evidence")
            + collect("sister-projects") + collect("country-studies") + collect("cross-industry")
            + collect("translations/en") + ["README.md"])
    docset = set(docs)
    doc_titles = {}
    for rp in sorted(docs):
        title, art, nav, lang = render_doc(rp, docset)
        doc_titles[rp] = title
        write(site_path(rp), page(title, art, nav, lang))
    print("rendered docs:", len(docs))

    gh = json.load(open(DATA, encoding="utf-8"))

    # case id -> source ledger file
    ledger = {}
    for f in docs:
        m = re.match(r"evidence/(CASE-\d+)-[^/]*source-ledger\.md$", f)
        if m:
            ledger[m.group(1)] = f

    def L(key_map):
        """Resolve quiz read keys -> {href,title} using doc titles where available."""
        out = {}
        for k, (label, rp) in key_map.items():
            href = site_path(rp) if rp in docset else f"{REPO_URL}/blob/main/{rp}"
            out[k] = {"h": href, "t": doc_titles.get(rp, label) or label}
        return out

    # ---- index ----
    cases = [f for f in docs if re.match(r"cases/CASE-", f)]
    claims = [f for f in docs if f.startswith("claims/C") and "README" not in f]
    chaps = sorted(f for f in docs if f.startswith("book/chapters/") and "README" not in f)
    profs = sorted(f for f in docs if f.startswith("book/profiles/") and "README" not in f)
    routes = sorted(f for f in docs if f.startswith("book/life-routes/") and "README" not in f)
    notes = [f for f in docs if f.startswith("book/research-notes/") and "README" not in f]

    stats = [
        (str(len(cases)), "编号研究案例"),
        (str(len(ledger)), "案例证据台账"),
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
        chap_cards += f'''<a class="card" href="{site_path(f)}"><span class="bignum">{num}</span><span class="tag">第 {num} 章</span><h3>{html.escape(t)}</h3><p>{html.escape(teaser)}</p></a>'''

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
<h1>独立游戏英雄传说<span class="stamp">传</span></h1>
<div class="en">那些本来"做不起游戏"的人，究竟是怎样把游戏做出来的</div>
<blockquote class="quote">不包装天才神话，不把"坚持"和"运气"当答案——追踪的是开工前会什么、靠什么活下来、失败如何变成下一作的资产、以及什么能复制、什么不能。</blockquote>
<div class="byline">作者 / 主创：洪荒行者 · Sparky（TrojanFighter） · Wunderwaffe Development</div>
<img class="heroart" src="/assets/hero.webp" alt="木刻题图：伏案的独立开发者，屏幕里是自己的游戏，远山之上飘着骑士旗">
<div class="stats">{stat_html}</div>
</div></header>

<section class="sect"><div class="wrap">
<h2>怎么进这本书<small>读人生，查证据，或先定位自己</small></h2>
<p class="lede">第一次来只想读人和故事，走第一张卡；想核每句话的证据强度，走第二张；不确定自己该读谁，先做三题问答。</p>
<div class="gate">
<a class="card" href="/book/START-HERE.html"><span class="tag">读者入口</span><h3>第一次来，先从这里读 →</h3><p>按现实问题组织：不知道该做什么、该不该辞职、没钱怎么办、失败还有没有意义。七篇跨人物章节 + 十四篇人物传记。</p></a>
<a class="card" href="/atlas.html"><span class="tag">研究后台</span><h3>案例地图与证据台账 →</h3><p>63 个编号 Case 档案、15 个可证伪命题、逐案的证据台账、反例与禁止外推。每句话都能追来源。</p></a>
<a class="card" href="/router.html"><span class="tag">互动工具</span><h3>你的处境 → 该先读谁 →</h3><p>三步问答（已有能力 / 风险处境 / 这次想移动什么），按 DECISION-ROUTER 原文的规则落到推荐书目。</p></a>
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
        cards += f'<a class="card" href="{site_path(f)}"><span class="bignum">{num}</span><span class="tag">第 {num} 章</span><h3>{html.escape(t)}</h3><p>{html.escape(teaser)}</p></a>'
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
        led = f'<td class="id"><a href="{site_path(ledger[cid])}">台账</a></td>' if cid in ledger else '<td class="id" style="color:var(--faint)">—</td>'
        trs += f'<tr><td class="id"><a href="{site_path(link)}">{cid}</a></td><td>{html.escape(subj)}</td><td>{html.escape(blurb)}</td>{led}</tr>'
    body = f'''<section class="sect"><div class="wrap">
<h2>案例地图<small>{n_cases} 个编号 Case</small></h2>
<p class="lede">Case ID 用于审计，不代表证据成熟度或推荐阅读顺序。带"待核"标记的对象尚未全部核实生产史与独立资格；「台账」列进该案的来源清单（P0/P1/S1/S2/H）。</p>
<input class="filter" id="f" placeholder="筛选案例：编号 / 游戏名 / 关键词…" oninput="q(this.value)">
<table class="atlas" id="t"><tr><th>Case</th><th>对象</th><th>它主要让我们看见什么</th><th>证据</th></tr>{trs}</table>
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
        trs += f'<tr><td class="id">{cell}</td><td><span class="status st-{st.lower()}">{st}</span></td><td>{html.escape(stmt)}</td></tr>'
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

    # ---- sections index: evidence ledgers + satellite programs + translations ----
    def grp_list(prefix, excl_readme=False):
        fs = [f for f in docs if f.startswith(prefix)]
        if excl_readme:
            fs = [f for f in fs if "README" not in f]
        fs.sort(key=lambda f: (0 if f.endswith("README.md") else 1, f))
        return fs
    groups = [
        ("案例证据台账", "每个 Case 的来源清单：URL、作者/机构、日期、证据等级（P0/P1/S1/S2/H）与对应事实。", grp_list("evidence/")),
        ("斯拉夫游戏英雄传说 · 姊妹篇", "同一套方法论下的东欧 / 俄语区游戏产业研究（Wargaming、GSC、IL-2 等）。", grp_list("sister-projects/")),
        ("中国国情研究", "教育、社会化与制度环境怎样影响创作者的生产条件。", grp_list("country-studies/")),
        ("跨行业研究", "工业革命比较实验室与创新者研究；不计入独立篇 Case 统计。", grp_list("cross-industry/")),
        ("English translations", "社区翻译层——目前覆盖有限，新译稿随仓库更新自动接入。", grp_list("translations/en/")),
    ]
    sec_html = ""
    for gname, gdesc, files in groups:
        lis = "".join(f'<li><a href="{site_path(f)}">{html.escape(doc_titles.get(f, f))}</a></li>' for f in files)
        sec_html += f'<div class="sect-grp"><h3>{gname}<span class="pill">{len(files)}</span></h3><div class="gd">{gdesc}</div><ul>{lis}</ul></div>'
    body = f'''<section class="sect"><div class="wrap">
<h2>分区<small>证据层与外围研究</small></h2>
<p class="lede">主书之外的证据层和研究分区：逐案台账、斯拉夫姊妹篇、中国国情、跨行业与英文翻译。研究对象按“它正在回答什么问题”路由（PROGRAM-MAP）。</p>
<input class="filter" placeholder="筛选全部分区文档…" oninput="q(this.value)">
<div id="t">{sec_html}</div>
</div></section>
<script>function q(v){{v=v.toLowerCase();document.querySelectorAll('#t li').forEach(r=>{{r.style.display=r.innerText.toLowerCase().includes(v)?'':'none'}})}}</script>'''
    write("/sections.html", page("分区", body, "n_sec"))

    # ---- interactive decision router ----
    READ_KEYS = {
        "gunpoint": ("Gunpoint / Tom Francis 人物稿", "book/profiles/gunpoint.md"),
        "wehle": ("The First Tree / David Wehle 人物稿", "book/profiles/david-wehle-first-tree.md"),
        "c42": ("CASE-042 The First Tree 研究档案", "cases/CASE-042-the-first-tree.md"),
        "c43": ("CASE-043 Everything / David OReilly", "cases/CASE-043-everything-david-oreilly.md"),
        "zach": ("Zachtronics / Zach Barth 人物稿", "book/profiles/zach-barth-zachtronics.md"),
        "c51": ("CASE-051 Zachtronics 研究档案", "cases/CASE-051-zachtronics.md"),
        "c45": ("CASE-045 RimWorld / Tynan Sylvester", "cases/CASE-045-rimworld.md"),
        "c54": ("CASE-054 Limit Theory / FIT-TRAP", "cases/CASE-054-limit-theory-fit-trap.md"),
        "c55": ("CASE-055 Factorio / 停止条件", "cases/CASE-055-factorio-stop-conditions.md"),
        "ch06": ("第六篇：你缺的真是一支团队吗？", "book/chapters/06-you-do-not-need-a-standard-studio.md"),
        "lr4": ("LR-004 项目已定但能力不足", "book/life-routes/project-thesis-capability-gap-004.md"),
        "nomada": ("Nomada / GRIS 人物稿", "book/profiles/nomada-gris-neva.md"),
        "c50": ("CASE-050 Nomada 研究档案", "cases/CASE-050-nomada-gris-neva.md"),
        "playdead": ("CASE-056 Playdead 创始人治理", "cases/CASE-056-playdead-founder-governance.md"),
        "c47": ("CASE-047 The Witness", "cases/CASE-047-the-witness.md"),
        "c49": ("CASE-049 Outer Wilds", "cases/CASE-049-outer-wilds.md"),
        "c52": ("CASE-052 House House / Big Walk", "cases/CASE-052-house-house-goose-game.md"),
        "c57": ("CASE-057 thatgamecompany / 股权扩张", "cases/CASE-057-thatgamecompany-vc-equity-expansion.md"),
        "c20": ("CASE-020 Into the Breach / Subset", "cases/CASE-020-into-the-breach.md"),
        "c36": ("CASE-036 Manor Lords", "cases/CASE-036-manor-lords.md"),
        "c53": ("CASE-053 Kenny Sun", "cases/CASE-053-kenny-sun.md"),
        "kenshi": ("Kenshi 人物稿", "book/profiles/kenshi.md"),
        "sv": ("Stardew Valley 人物稿", "book/profiles/stardew-valley.md"),
        "c04": ("CASE-004 Stardew Valley 研究档案", "cases/CASE-004-stardew-valley.md"),
        "ftl": ("FTL 人物稿", "book/profiles/ftl.md"),
        "rl": ("Rocket League / Psyonix 人物稿", "book/profiles/rocket-league.md"),
        "c09": ("CASE-009 Project Wingman", "cases/CASE-009-project-wingman.md"),
        "c23": ("CASE-023 despelote", "cases/CASE-023-despelote.md"),
        "c25": ("CASE-025 Bills Must Be Paid", "cases/CASE-025-bills-must-be-paid.md"),
        "c58": ("CASE-058 Spiderweb / FIT-LOCK-IN", "cases/CASE-058-spiderweb-fit-lock-in.md"),
        "c60": ("CASE-060 Croteam / 分阶段脱出", "cases/CASE-060-croteam-staged-lockin-escape.md"),
        "lridx": ("Life Risk Routes 全部路线", "book/life-routes/README.md"),
        "arch": ("按主创者能力进入", "book/READER-ARCHETYPES.md"),
        "router": ("DECISION-ROUTER 完整原文", "book/DECISION-ROUTER.md"),
    }
    R = L(READ_KEYS)
    QUIZ = [
        {"k":"cap","title":"第一步 · 你已经能做什么，还缺什么？","desc":"同一个『程序员』处境可能完全不同，先定位能力结构。","multi":False,"opts":[
            {"k":"A","b":"我有一个明显强项，但项目还没定","s":"程序 / 技术美术 / 视觉 / 写作 / 世界构建 / 系统设计，或 mod、UGC、服务器运营经验","reads":["gunpoint","wehle","c42","c43","zach","c51","c45","c54","c55"],"note":"SHAPE——先问：有没有一种项目形态，会让我的强项成为玩家价值，而不只是生产便利？Limit Theory 与 Factorio 是对照：强项也可能让人选错问题。"},
            {"k":"B","b":"我已经有清楚的作品方向，但缺关键能力","s":"视觉作者缺技术、程序员缺美术 / 制作管理、设计者一个人做不完","reads":["ch06","lr4","nomada","c50","playdead","c47","c49","c52","c57","c20","c36"],"note":"三条补齐路线成本完全不同：COMPOSE（共同创始人）、EXPAND（用资金）、PERIPHERALIZE（专业协作者）——到第三步选你要比较的那种。"},
            {"k":"C","b":"我什么都会一点，但没有明显单项护城河","s":"关键看是更快做出作品并获得反馈，还是一个人硬扛全部岗位","reads":["c53","kenshi","sv","c04","ftl","c25"],"note":"区分三种过程：劳动压缩 / 重新定义项目 / 逐步积累能力（ACCRETE）。连续练习不保证同样结果。"},
            {"k":"D","b":"我已经成功过一次 / 手里有一笔资本","s":"资金能增加能力，也能买探索时间——警惕先变成更高固定支出","reads":["c20","c47","c52","c57"],"note":"两种用钱方式：BUY CAPABILITY（雇人获得能力）vs BUY OPTIONALITY（保留选择与放弃空间）。"}],
        },
        {"k":"risk","title":"第二步 · 你的生活能承担什么风险？","desc":"能力相似，不代表风险承受力相似。","multi":False,"opts":[
            {"k":"R0","b":"我不能承受长期无收入","s":"无储蓄 / 房贷 / 孩子 / 赡养 / 签证医疗债务约束","reads":["gunpoint","wehle","c42","kenshi","rl"],"note":"在承担难以撤回的投入前，先做出可玩版、拿到陌生人反馈、核查市场证据。辞职的勇气不能替代这些信息。"},
            {"k":"R1","b":"能支持几个月到一年制作，但还没有强证据","s":"适合有边界的试验：投入多久、验证什么、什么结果会改变决定","reads":["ftl","c09","c23"],"note":"BOUNDED EXPERIMENT——在资金窗口耗尽前，拿到足以判断停项 / 继续 / 转向 / 向资方提案的外部证据。"},
            {"k":"R2","b":"有稳定工资、支出较低，可以慢慢试","s":"低支出延长试错，也可能让错误维持更久","reads":["gunpoint","wehle","c42","c53"],"note":"检查：阶段截止期限、陌生人反馈、能否缩小范围、什么情况停止、业余项目留下了什么能力。"},
            {"k":"R3","b":"已有前作收入 / 组织现金流 / 很高退出能力","s":"资源可以买探索时间，也可以加人手——先分清缺哪个","reads":["c20","c47","c52"],"note":"先问：现在缺的是更多人手，还是更多尝试不同方向的时间？"},
            {"k":"R4","b":"准备与发行商、股权投资者或共同创始人合作","s":"会增加资源，也会改变决定怎样作出、权利怎样分配","reads":["c49","nomada","c50","playdead","c57"],"note":"至少查清：谁持股、谁在董事会、谁能停项目、谁定发售、谁拥有知识产权、回报与义务由谁承担。"}],
        },
        {"k":"move","title":"第三步 · 这次到底应该移动什么？（可多选）","desc":"把真实问题对上调整变量；每条都带需要检查的风险。","multi":True,"opts":[
            {"k":"SHAPE","b":"强项明显，项目未定 → 围绕能力形成作品","s":"强项是否使你选错问题","reads":["gunpoint","wehle","zach"]},
            {"k":"COMPOSE","b":"方向明确，缺共同核心能力 → 与共同创始人组合","s":"治理、股份与作者权利","reads":["nomada","playdead"]},
            {"k":"EXPAND","b":"体验已验证，缺生产能力 → 用资金获得能力","s":"支出、控制权与后续资金依赖","reads":["c47","c49","c52","c57"]},
            {"k":"ACCRETE","b":"多种技能未成熟 → 用连续项目积累","s":"一直练习却不接受市场检验","reads":["c53","c25"]},
            {"k":"STOP","b":"技术强，局部问题无限多 → 明确做到什么程度就够","s":"引擎进展是否转成产品进展","reads":["c55","c54"]},
            {"k":"PRESERVE","b":"第一次成功，选择变多 → 保留探索与放弃空间","s":"过早增加固定支出","reads":["c20","c52"]},
            {"k":"AUDIT","b":"多年固定制作方式 → 核对转型限制","s":"切换成本与新受众的建立","reads":["c51","c58"]},
            {"k":"ESCAPE","b":"想从成熟制作路线转出 → 分开改变不同层面","s":"个案不能证明普遍规律；2014 与 2023 所有权不同","reads":["c60","c51","c58"]}],
        },
    ]
    import json as _json
    data_js = "var R=" + _json.dumps(R, ensure_ascii=False) + ";\nvar STEPS=" + _json.dumps(QUIZ, ensure_ascii=False) + ";"
    body = f'''<section class="sect"><div class="col" style="max-width:820px">
<h2 style="font-size:26px;font-weight:900;margin-bottom:6px">决策路由 · 互动版</h2>
<p class="lede">三题问答：已有能力 → 风险处境 → 这次想移动什么。推荐规则逐字取自 <a href="/book/DECISION-ROUTER.html">DECISION-ROUTER 原文</a>——它给的是“先读谁、先比什么”，不是替你决定。</p>
<div id="quiz"></div>
<div class="qz-res" id="res"><h3>建议你先读这些</h3><div id="resin"></div></div>
</div></section>
<script>
{data_js}
var ans={{}},msel={{}};STEPS.forEach(function(s){{msel[s.k]={{}}}});
var qz=document.getElementById('quiz'),res=document.getElementById('res'),resin=document.getElementById('resin');
STEPS.forEach(function(s,si){{
var st=document.createElement('div');st.className='qz-step';
st.innerHTML='<h3>'+s.title+'</h3><div class="qd">'+s.desc+'</div>';
s.opts.forEach(function(o){{
var b=document.createElement('button');b.className='qz-opt';b.dataset.k=o.k;b.dataset.s=s.k;
b.innerHTML='<b>'+o.k+' · '+o.b+'</b><span>'+o.s+'</span>';
b.onclick=function(){{
if(s.multi){{msel[s.k][o.k]=!msel[s.k][o.k];b.classList.toggle('sel',msel[s.k][o.k]);}}
else{{ans[s.k]=o.k;st.querySelectorAll('.qz-opt').forEach(function(x){{x.classList.toggle('sel',x.dataset.k===o.k)}});}}
res_r();}};
st.appendChild(b);}});
qz.appendChild(st);}});
function res_r(){{
var out='',any=false;
STEPS.forEach(function(s){{
var ks=s.multi?s.opts.filter(function(o){{return msel[s.k][o.k]}}).map(function(o){{return o.k}}):(ans[s.k]?[ans[s.k]]:[]);
ks.forEach(function(ok){{var o=s.opts.filter(function(x){{return x.k===ok}})[0];any=true;
out+='<h4>'+s.title.split(' · ')[0]+' → '+o.k+'</h4>';
if(o.note)out+='<div class="qz-note">'+o.note+'</div>';
out+='<ul>'+o.reads.map(function(r){{return '<li><a href="'+R[r].h+'">'+R[r].t+'</a></li>'}}).join('')+'</ul>';
if(s.multi)out+='<div class="qn">⚠ 需要检查：'+o.s+'</div>';}});}});
if(!any){{res.style.display='none';return}}
out+='<div class="qz-warn">四个误用警告：① 不要只按职业认领案例；② 不要只按年龄认领案例——比较家庭支出、债务、医疗签证、再就业条件；③ 不要把成功结果倒写成正确动作（哪一年？什么平台？什么融资环境？）；④ 至少匹配两个坐标（能力缺口 / 风险时间 / 项目阶段 / 市场接入 / 治理）再谈“这个案例像我”。</div>';
out+='<h4>还可以继续</h4><ul><li><a href="'+R.lridx.h+'">'+R.lridx.t+'</a> —— LR-001 至 LR-005，按具体人生处境读</li><li><a href="'+R.arch.h+'">'+R.arch.t+'</a> —— 按职业/能力结构找人物</li><li><a href="'+R.router.h+'">'+R.router.t+'</a></li></ul>';
resin.innerHTML=out;res.style.display='block';res.scrollIntoView({{behavior:'smooth',block:'nearest'}});
}}
</script>'''
    write("/router.html", page("决策路由 · 互动版", body, "n_rt"))

    print("done ->", OUT)

if __name__ == "__main__":
    main()
