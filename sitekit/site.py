"""Generate the static site from data/repos.json, site.json and content/*.md."""

from __future__ import annotations

import datetime as dt
import email.utils
import html
import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from . import markdown as md

AI_CRAWLERS = ("GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended")


@dataclass
class Post:
    slug: str
    title: str
    date: str
    description: str
    body_md: str

    @property
    def path(self) -> str:
        return f"/posts/{self.slug}/"


@dataclass
class Site:
    cfg: dict
    data: dict
    posts: list[Post] = field(default_factory=list)

    @property
    def url(self) -> str:
        return self.cfg["url"].rstrip("/")

    def abs(self, path: str) -> str:
        return self.url + path

    @property
    def repos(self) -> list[dict]:
        return self.data["repos"]

    def repo(self, name: str) -> dict | None:
        return next((r for r in self.repos if r["name"] == name), None)

    def repo_href(self, repo: dict) -> str:
        """Where the site sends a reader for a repository: its own Pages site, else our page."""
        return repo.get("own_site") or f"/{repo['name']}/"

    def generated_repos(self) -> list[dict]:
        """Repositories that get a page here. A repo with its own Pages site at
        /<name>/ would shadow ours on github.io, so it is linked instead."""
        return [r for r in self.repos if not r.get("own_site")]


# ---------------------------------------------------------------- loading

def load_posts(content_dir: Path) -> list[Post]:
    posts = []
    for path in sorted(content_dir.glob("*.md")):
        meta, body = md.split_front_matter(path.read_text(encoding="utf-8"))
        slug = meta.get("slug") or re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
        title = meta.get("title", "")
        lines = body.lstrip("\n").split("\n")
        if lines and lines[0].startswith("# "):  # the H1 is the page title
            title = title or lines[0][2:].strip()
            body = "\n".join(lines[1:])
        date = meta.get("date", "")
        dt.date.fromisoformat(date)  # fail loudly on a bad date
        if not title:
            raise ValueError(f"{path}: post has no title")
        posts.append(Post(slug, title, date, meta.get("description") or md.first_paragraph_text(body), body.strip() + "\n"))
    posts.sort(key=lambda p: (p.date, p.slug), reverse=True)
    return posts


def load_site(root: Path, data_path: Path | None = None, content_dir: Path | None = None) -> Site:
    cfg = json.loads((root / "site.json").read_text(encoding="utf-8"))
    data = json.loads((data_path or root / "data" / "repos.json").read_text(encoding="utf-8"))
    return Site(cfg, data, load_posts(content_dir or root / "content"))


# ---------------------------------------------------------------- helpers

def esc(text: str) -> str:
    return html.escape(text, quote=True)


def plain(text_md: str) -> str:
    """Markdown one-liner to plain text."""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text_md)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    return " ".join(re.sub(r"[`*]", "", text).split())


def jsonld(obj: dict) -> str:
    raw = json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=False)
    raw = raw.replace("</", "<\\/")  # never close the script element early
    return f'<script type="application/ld+json">\n{raw}\n</script>'


def latest_release(repo: dict) -> dict | None:
    rels = repo.get("releases") or []
    return rels[0] if rels else None


def license_url(repo: dict) -> str:
    spdx = repo.get("license") or ""
    if spdx and spdx not in ("NOASSERTION", "OTHER"):
        return f"https://spdx.org/licenses/{spdx}.html"
    return f"{repo['html_url']}/blob/{repo.get('default_branch', 'main')}/LICENSE"


def rfc822(date: str) -> str:
    d = dt.date.fromisoformat(date[:10])
    return email.utils.format_datetime(dt.datetime(d.year, d.month, d.day, tzinfo=dt.UTC))


def person(site: Site) -> dict:
    return {"@type": "Person", "name": site.cfg["author"], "url": site.url + "/", "sameAs": [site.cfg["github"]]}


# ---------------------------------------------------------------- layout

def page(site: Site, *, path: str, title: str, description: str, body: str,
         ld: list[dict] | None = None, og_type: str = "website", noindex: bool = False) -> str:
    full_title = title if title == site.cfg["title"] else f"{title} | {site.cfg['title']}"
    canonical = site.abs(path)
    head = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{esc(full_title)}</title>",
        f'<meta name="description" content="{esc(description)}">',
        f'<meta name="author" content="{esc(site.cfg["author"])}">',
        '<meta name="color-scheme" content="dark light">',
        '<meta name="theme-color" content="#0A1628">',
    ]
    if noindex:
        head.append('<meta name="robots" content="noindex">')
    else:
        head.append(f'<link rel="canonical" href="{esc(canonical)}">')
    head += [
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(description)}">',
        f'<meta property="og:url" content="{esc(canonical)}">',
        f'<meta property="og:site_name" content="{esc(site.cfg["title"])}">',
        '<meta name="twitter:card" content="summary">',
        '<link rel="stylesheet" href="/style.css">',
        f'<link rel="alternate" type="application/rss+xml" title="{esc(site.cfg["title"])}" href="/feed.xml">',
        '<link rel="alternate" type="text/plain" title="llms.txt" href="/llms.txt">',
    ]
    for obj in ld or []:
        head.append(jsonld({"@context": "https://schema.org", **obj}))
    nav = (
        '<header class="top"><nav aria-label="Site">'
        f'<a class="home" href="/">{esc(site.cfg["author"])}</a>'
        '<a href="/#projects">Projects</a><a href="/posts/">Posts</a>'
        f'<a href="{esc(site.cfg["github"])}">GitHub</a>'
        "</nav></header>"
    )
    foot = (
        '<footer><p>Code on this site is MIT licensed; posts are '
        '<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. '
        f'Source: <a href="{esc(site.cfg["source"])}">{esc(site.cfg["source"].split("github.com/")[-1])}</a>. '
        'No analytics, no cookies, no scripts.</p>'
        '<p><a href="/feed.xml">RSS</a> · <a href="/llms.txt">llms.txt</a> · <a href="/sitemap.xml">Sitemap</a></p></footer>'
    )
    return (
        "<!doctype html>\n"
        f'<html lang="{site.cfg.get("lang", "en")}">\n<head>\n' + "\n".join(head) + "\n</head>\n"
        f"<body>\n{nav}\n<main>\n{body}\n</main>\n{foot}\n</body>\n</html>\n"
    )


# ---------------------------------------------------------------- pages

def render_home(site: Site) -> str:
    parts = [f'<h1>{esc(site.cfg["author"])}</h1>', f'<p class="lede">{esc(site.cfg["bio"])}</p>']
    parts.append('<section id="projects" aria-labelledby="projects-h"><h2 id="projects-h">Projects</h2>')
    for theme in site.data["themes"]:
        repos = [site.repo(n) for n in theme["repos"] if site.repo(n)]
        if not repos:
            continue
        tid = md.slugify(theme["title"])
        parts.append(f'<h3 id="{tid}">{esc(theme["title"])}</h3>')
        parts.append('<table class="repos"><thead><tr><th scope="col">Repository</th><th scope="col">What it is</th></tr></thead><tbody>')
        for r in repos:
            parts.append(
                f'<tr><td><a href="{esc(site.repo_href(r))}">{esc(r["name"])}</a></td>'
                f'<td>{md.inline(r["one_liner"])}</td></tr>'
            )
        parts.append("</tbody></table>")
    parts.append("</section>")

    rels = sorted(
        ((r, latest_release(r)) for r in site.repos if latest_release(r)),
        key=lambda x: (x[1]["date"], x[0]["name"]), reverse=True,
    )[: site.cfg.get("home_releases", 8)]
    parts.append('<section aria-labelledby="releases-h"><h2 id="releases-h">Latest releases</h2>')
    if rels:
        parts.append('<table class="releases"><thead><tr><th scope="col">Project</th><th scope="col">Release</th>'
                     '<th scope="col">Published</th></tr></thead><tbody>')
        for r, rel in rels:
            parts.append(
                f'<tr><td><a href="{esc(site.repo_href(r))}">{esc(r["name"])}</a></td>'
                f'<td><a href="{esc(rel["url"])}">{esc(rel["tag"])}</a></td>'
                f'<td><time datetime="{rel["date"]}">{rel["date"]}</time></td></tr>'
            )
        parts.append("</tbody></table>")
    else:
        parts.append("<p>No releases yet.</p>")
    owner = site.data["owner"]
    parts.append(
        f'<p>Packages: container images and npm packages are listed on '
        f'<a href="https://github.com/{owner}?tab=packages">the Packages tab</a>.</p></section>'
    )

    parts.append('<section aria-labelledby="posts-h"><h2 id="posts-h">Posts</h2>')
    parts.append(post_list(site.posts) if site.posts else "<p>No posts yet.</p>")
    parts.append("</section>")

    ld = [
        {"@type": "WebSite", "name": site.cfg["title"], "url": site.url + "/", "author": person(site)},
        {**person(site), "description": site.cfg["bio"]},
    ]
    return page(site, path="/", title=site.cfg["title"], description=site.cfg["description"], body="\n".join(parts), ld=ld)


def post_list(posts: list[Post]) -> str:
    items = "".join(
        f'<li><a href="{p.path}">{esc(p.title)}</a> <time datetime="{p.date}">{p.date}</time>'
        f"<br><span class=\"muted\">{esc(p.description)}</span></li>"
        for p in posts
    )
    return f'<ul class="posts">{items}</ul>'


def render_repo(site: Site, r: dict) -> str:
    owner = site.data["owner"]
    rel = latest_release(r)
    parts = [
        f'<p class="crumbs"><a href="/">Home</a> / <a href="/#{md.slugify(r["theme"])}">{esc(r["theme"])}</a></p>',
        f"<h1>{esc(r['name'])}</h1>",
        f'<p class="lede">{md.inline(r["one_liner"])}</p>',
        '<p class="meta">'
        + " · ".join(esc(x) for x in [r.get("language") or "", r.get("license") or "", f"latest {rel['tag']}" if rel else "no release yet"] if x)
        + "</p>",
    ]
    if r.get("intro_md"):
        parts.append('<section aria-labelledby="what-h"><h2 id="what-h">What it is</h2>')
        parts.append(md.convert(r["intro_md"], heading_offset=2, heading_ids=False))
        parts.append("</section>")
    if r.get("install"):
        lang = r["install"].get("lang") or "bash"
        parts.append('<section aria-labelledby="install-h"><h2 id="install-h">Install</h2>')
        parts.append(f'<pre><code class="language-{esc(lang)}">{esc(r["install"]["code"])}</code></pre>')
        readme = esc(r["html_url"]) + "#readme"
        parts.append(f'<p class="muted">From the README; see <a href="{readme}">the full README</a> for every option.</p></section>')
    links = [
        ("Repository", r["html_url"]),
        ("Releases", f"{r['html_url']}/releases"),
        ("Packages", f"https://github.com/{owner}?tab=packages&repo_name={r['name']}"),
        ("Issues", f"{r['html_url']}/issues"),
    ]
    if r.get("homepage") and site.url not in r["homepage"]:
        links.append(("Homepage", r["homepage"]))
    parts.append('<section aria-labelledby="links-h"><h2 id="links-h">Links</h2><ul class="links">')
    parts += [f'<li><a href="{esc(u)}">{esc(t)}</a></li>' for t, u in links]
    parts.append("</ul></section>")
    if r.get("releases"):
        parts.append('<section aria-labelledby="rel-h"><h2 id="rel-h">Releases</h2><ul>')
        for x in r["releases"]:
            label = x["tag"] if not x.get("name") or x["name"] == x["tag"] else f'{x["tag"]}: {x["name"]}'
            parts.append(f'<li><a href="{esc(x["url"])}">{esc(label)}</a> <time datetime="{x["date"]}">{x["date"]}</time></li>')
        parts.append("</ul></section>")
    if r.get("topics"):
        parts.append('<p class="topics">Topics: ' + ", ".join(esc(t) for t in r["topics"]) + "</p>")

    code = {
        "@type": "SoftwareSourceCode",
        "name": r["name"],
        "description": r["description"],
        "url": site.abs(f"/{r['name']}/"),
        "codeRepository": r["html_url"],
        "programmingLanguage": r.get("language") or "Unknown",
        "license": license_url(r),
        "author": person(site),
    }
    if r.get("topics"):
        code["keywords"] = ", ".join(r["topics"])
    if rel:
        code["version"] = rel["tag"].lstrip("v")
        code["dateModified"] = rel["date"]
    return page(site, path=f"/{r['name']}/", title=r["name"], description=r["description"], body="\n".join(parts), ld=[code])


def render_post(site: Site, p: Post) -> str:
    body = (
        f'<p class="crumbs"><a href="/">Home</a> / <a href="/posts/">Posts</a></p>'
        f'<article><h1>{esc(p.title)}</h1>'
        f'<p class="meta">By {esc(site.cfg["author"])} · <time datetime="{p.date}">{p.date}</time></p>\n'
        f"{md.convert(p.body_md, heading_offset=1)}\n</article>"
    )
    ld = {
        "@type": "BlogPosting",
        "headline": p.title,
        "description": p.description,
        "datePublished": p.date,
        "dateModified": p.date,
        "url": site.abs(p.path),
        "mainEntityOfPage": site.abs(p.path),
        "author": person(site),
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "inLanguage": site.cfg.get("lang", "en"),
    }
    return page(site, path=p.path, title=p.title, description=p.description, body=body, ld=[ld], og_type="article")


def render_posts_index(site: Site) -> str:
    body = '<p class="crumbs"><a href="/">Home</a></p><h1>Posts</h1>' + (post_list(site.posts) if site.posts else "<p>No posts yet.</p>")
    return page(site, path="/posts/", title="Posts", description=f"Posts by {site.cfg['author']}.", body=body)


def render_404(site: Site) -> str:
    body = (
        "<h1>Page not found</h1><p>That page does not exist. The <a href=\"/\">home page</a> lists every project, "
        f'and every repository is also on <a href="{esc(site.cfg["github"])}">GitHub</a>.</p>'
    )
    return page(site, path="/404.html", title="Page not found", description="Page not found.", body=body, noindex=True)


# ---------------------------------------------------------------- text outputs

def site_pages(site: Site) -> list[tuple[str, str | None]]:
    """(path, lastmod) for every indexable page, in sitemap order."""
    dates = [p.date for p in site.posts] + [rel["date"] for r in site.repos if (rel := latest_release(r))]
    pages: list[tuple[str, str | None]] = [("/", max(dates) if dates else None)]
    pages.append(("/posts/", site.posts[0].date if site.posts else None))
    pages += [(p.path, p.date) for p in site.posts]
    for r in site.generated_repos():
        rel = latest_release(r)
        pages.append((f"/{r['name']}/", rel["date"] if rel else None))
    return pages


def render_sitemap(site: Site) -> str:
    rows = []
    for path, lastmod in site_pages(site):
        lm = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
        rows.append(f"  <url><loc>{esc(site.abs(path))}</loc>{lm}</url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(rows) + "\n</urlset>\n")


def render_robots(site: Site) -> str:
    blocks = ["User-agent: *\nAllow: /\n"] + [f"User-agent: {a}\nAllow: /\n" for a in AI_CRAWLERS]
    return "\n".join(blocks) + f"\nSitemap: {site.abs('/sitemap.xml')}\n"


def render_feed(site: Site) -> str:
    items = []
    for p in site.posts:
        items.append((p.date, f"{p.title}", site.abs(p.path), p.description))
    for r in site.repos:
        for rel in (r.get("releases") or [])[:3]:
            items.append((rel["date"], f"{r['name']} {rel['tag']}", rel["url"], f"Release {rel['tag']} of {r['name']}: {plain(r['one_liner'])}"))
    items.sort(key=lambda x: (x[0], x[1]), reverse=True)
    items = items[: site.cfg.get("feed_items", 30)]
    last = rfc822(items[0][0]) if items else rfc822("2026-10-04")
    xml_items = "".join(
        f"\n  <item><title>{esc(t)}</title><link>{esc(u)}</link><guid isPermaLink=\"true\">{esc(u)}</guid>"
        f"<pubDate>{rfc822(d)}</pubDate><description>{esc(desc)}</description></item>"
        for d, t, u, desc in items
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n<channel>\n'
        f"  <title>{esc(site.cfg['title'])}</title>\n  <link>{site.url}/</link>\n"
        f"  <description>{esc(site.cfg['description'])}</description>\n  <language>{site.cfg.get('lang', 'en')}</language>\n"
        f"  <lastBuildDate>{last}</lastBuildDate>\n"
        f'  <atom:link href="{site.abs("/feed.xml")}" rel="self" type="application/rss+xml"/>'
        f"{xml_items}\n</channel>\n</rss>\n"
    )


def absolute(site: Site, href: str) -> str:
    return site.abs(href) if href.startswith("/") else href


def render_llms(site: Site) -> str:
    """llms.txt per llmstxt.org: H1, blockquote summary, prose, H2 sections of link lists."""
    out = [f"# {site.cfg['author']}", "", f"> {site.cfg['description']}", "", site.cfg["bio"], ""]
    for theme in site.data["themes"]:
        repos = [site.repo(n) for n in theme["repos"] if site.repo(n)]
        if not repos:
            continue
        out.append(f"## {theme['title']}")
        out.append("")
        for r in repos:
            out.append(f"- [{r['name']}]({absolute(site, site.repo_href(r))}): {plain(r['one_liner'])}")
        out.append("")
    if site.posts:
        out += ["## Posts", ""]
        out += [f"- [{p.title}]({site.abs(p.path)}): {p.description}" for p in site.posts]
        out.append("")
    out += ["## Optional", "",
            f"- [Full text]({site.abs('/llms-full.txt')}): every project page and post in one file",
            f"- [Feed]({site.abs('/feed.xml')}): posts and releases as RSS", ""]
    return "\n".join(out)


def render_llms_full(site: Site) -> str:
    out = [f"# {site.cfg['author']}", "", f"> {site.cfg['description']}", "", site.cfg["bio"], ""]
    for theme in site.data["themes"]:
        for name in theme["repos"]:
            r = site.repo(name)
            if not r:
                continue
            out += [f"## {r['name']}", "", f"Page: {absolute(site, site.repo_href(r))}",
                    f"Repository: {r['html_url']}", f"Theme: {theme['title']}", "", plain(r["one_liner"]), ""]
            if r.get("intro_md"):
                out += [r["intro_md"].strip(), ""]
            if r.get("install"):
                out += ["Install:", "", f"```{r['install'].get('lang') or 'bash'}", r["install"]["code"], "```", ""]
            if (rel := latest_release(r)):
                out += [f"Latest release: {rel['tag']} ({rel['date']}) {rel['url']}", ""]
    for p in site.posts:
        out += [f"## Post: {p.title}", "", f"URL: {site.abs(p.path)}", f"Date: {p.date}", "", p.body_md.strip(), ""]
    return "\n".join(out)


# ---------------------------------------------------------------- build

def build(site: Site, out: Path, css: str) -> list[Path]:
    if out.exists():
        if any(out.iterdir()) and not (out / ".nojekyll").exists():
            raise SystemExit(f"refusing to clear {out}: it has files but no .nojekyll marker")
        shutil.rmtree(out)
    out.mkdir(parents=True)
    written: list[Path] = []

    def write(rel: str, text: str) -> None:
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        written.append(path)

    write(".nojekyll", "")
    write("style.css", css)
    write("index.html", render_home(site))
    write("posts/index.html", render_posts_index(site))
    for p in site.posts:
        write(f"posts/{p.slug}/index.html", render_post(site, p))
    for r in site.generated_repos():
        write(f"{r['name']}/index.html", render_repo(site, r))
    write("404.html", render_404(site))
    write("sitemap.xml", render_sitemap(site))
    write("robots.txt", render_robots(site))
    write("feed.xml", render_feed(site))
    write("llms.txt", render_llms(site))
    write("llms-full.txt", render_llms_full(site))
    write(f"{site.cfg['indexnow_key']}.txt", site.cfg["indexnow_key"] + "\n")
    return written
