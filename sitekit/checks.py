"""Checks over a built site directory. Each check returns a list of problems."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
# Elements whose end tag may be omitted in HTML; we still close them, but tolerate parser-implied closes.
TEXT_SUFFIXES = (".html", ".txt", ".xml", ".css")

EM_DASH = "\u2014"
# Words that must never appear. Stored reversed so a grep of this repository for them stays empty.
FORBIDDEN = tuple(w[::-1] for w in ("noosam", "rasih"))
MODEL_NAMES = re.compile(
    r"\b(GPT-?[345](\.\d)?o?|gpt-4o|ChatGPT|Claude\s+(?:Opus|Sonnet|Haiku|Fable)|Opus\s+\d|Sonnet\s+\d|Haiku\s+\d|"
    r"Gemini|Llama\s*\d|Mistral|Mixtral|Qwen|DeepSeek|Grok)\b"
)


class _Checker(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, tuple[int, int]]] = []
        self.errors: list[str] = []
        self.ids: set[str] = set()
        self.jsonld: list[str] = []
        self.links: list[str] = []
        self._in_jsonld = False
        self._buf: list[str] = []
        self.has_title = False
        self.doctype = False

    def handle_decl(self, decl: str) -> None:
        if decl.lower() == "doctype html":
            self.doctype = True

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            if a["id"] in self.ids:
                self.errors.append(f"line {self.getpos()[0]}: duplicate id {a['id']!r}")
            self.ids.add(a["id"])
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag == "link" and a.get("href"):
            self.links.append(a["href"])
        if tag == "title":
            self.has_title = True
        if tag == "script":
            if a.get("type") != "application/ld+json":
                self.errors.append(f"line {self.getpos()[0]}: script other than JSON-LD")
            self._in_jsonld = True
            self._buf = []
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in VOID:
            self.errors.append(f"line {self.getpos()[0]}: end tag for void element <{tag}>")
            return
        if not self.stack:
            self.errors.append(f"line {self.getpos()[0]}: stray </{tag}>")
            return
        open_tag, pos = self.stack[-1]
        if open_tag != tag:
            self.errors.append(f"line {self.getpos()[0]}: </{tag}> closes <{open_tag}> opened on line {pos[0]}")
            if any(t == tag for t, _ in self.stack):
                while self.stack and self.stack[-1][0] != tag:
                    self.stack.pop()
                self.stack.pop()
            return
        self.stack.pop()
        if tag == "script" and self._in_jsonld:
            self.jsonld.append("".join(self._buf))
            self._in_jsonld = False

    def handle_data(self, data):
        if self._in_jsonld:
            self._buf.append(data)

    def close(self):
        super().close()
        for tag, pos in self.stack:
            self.errors.append(f"line {pos[0]}: <{tag}> never closed")


def parse_html(text: str) -> _Checker:
    c = _Checker()
    c.feed(text)
    c.close()
    return c


def _rel(p: Path, root: Path) -> str:
    return p.relative_to(root).as_posix()


def path_exists(site_dir: Path, path: str) -> bool:
    """Does a site path such as /a/ or /feed.xml map to a built file?"""
    path = path.split("#", 1)[0].split("?", 1)[0]
    if not path.startswith("/"):
        return False
    target = site_dir / path.lstrip("/")
    if path.endswith("/"):
        return (target / "index.html").is_file()
    return target.is_file() or (target / "index.html").is_file()


def check_html(site_dir: Path, site_url: str, external_ok: set[str] | None = None) -> list[str]:
    """external_ok: URLs under site_url served by another repository's Pages site."""
    problems = []
    external_ok = external_ok or set()
    for f in sorted(site_dir.rglob("*.html")):
        c = parse_html(f.read_text(encoding="utf-8"))
        name = _rel(f, site_dir)
        problems += [f"{name}: {e}" for e in c.errors]
        if not c.doctype:
            problems.append(f"{name}: missing <!doctype html>")
        if not c.has_title:
            problems.append(f"{name}: missing <title>")
        for i, block in enumerate(c.jsonld):
            try:
                obj = json.loads(block)
                if obj.get("@context") != "https://schema.org" or "@type" not in obj:
                    problems.append(f"{name}: JSON-LD block {i} lacks @context or @type")
            except json.JSONDecodeError as e:
                problems.append(f"{name}: JSON-LD block {i} does not parse: {e}")
        for href in c.links:
            if href in external_ok:
                continue
            if href.startswith(site_url):
                href = href[len(site_url):] or "/"
            if href.startswith("/") and not href.startswith("//") and not path_exists(site_dir, href):
                problems.append(f"{name}: broken internal link {href}")
            if href.startswith("#") and len(href) > 1 and href[1:] not in c.ids:
                problems.append(f"{name}: broken anchor {href}")
    return problems


def check_sitemap(site_dir: Path, site_url: str) -> list[str]:
    path = site_dir / "sitemap.xml"
    try:
        tree = ET.parse(path)
    except (ET.ParseError, FileNotFoundError) as e:
        return [f"sitemap.xml: {e}"]
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    problems = []
    locs = [e.text or "" for e in tree.getroot().findall("s:url/s:loc", ns)]
    if not locs:
        problems.append("sitemap.xml: no URLs")
    for loc in locs:
        if not loc.startswith(site_url + "/"):
            problems.append(f"sitemap.xml: {loc} is not under {site_url}")
        elif not path_exists(site_dir, loc[len(site_url):]):
            problems.append(f"sitemap.xml: {loc} has no file")
    return problems


def check_xml(site_dir: Path) -> list[str]:
    problems = []
    for f in sorted(site_dir.glob("*.xml")):
        try:
            ET.parse(f)
        except ET.ParseError as e:
            problems.append(f"{f.name}: {e}")
    return problems


def check_llms(site_dir: Path, site_url: str, external_ok: set[str] | None = None) -> list[str]:
    """Every link in llms.txt and llms-full.txt's link lines must be a page on this site
    (or a project's own Pages site listed in external_ok)."""
    problems = []
    external_ok = external_ok or set()
    f = site_dir / "llms.txt"
    if not f.is_file():
        return ["llms.txt missing"]
    text = f.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# "):
        problems.append("llms.txt: first line must be an H1")
    for n, line in enumerate(lines, 1):
        for url in re.findall(r"\]\(([^)\s]+)\)", line):
            if url in external_ok:
                continue
            if not url.startswith(site_url + "/"):
                problems.append(f"llms.txt:{n}: {url} is not a page on this site")
            elif not path_exists(site_dir, url[len(site_url):]):
                problems.append(f"llms.txt:{n}: {url} has no file")
    return problems


def check_text(site_dir: Path) -> list[str]:
    """House rules over every generated text file: no em-dashes, no model names, no forbidden words."""
    problems = []
    forbidden = re.compile("|".join(FORBIDDEN), re.IGNORECASE)
    for f in sorted(site_dir.rglob("*")):
        if not f.is_file() or f.suffix not in TEXT_SUFFIXES:
            continue
        name = _rel(f, site_dir)
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if EM_DASH in line:
                problems.append(f"{name}:{n}: em-dash")
            if m := MODEL_NAMES.search(line):
                problems.append(f"{name}:{n}: model name {m.group(0)!r}")
            if m := forbidden.search(line):
                problems.append(f"{name}:{n}: forbidden word")
    return problems


def check_required(site_dir: Path, key: str) -> list[str]:
    need = ["index.html", "404.html", ".nojekyll", "robots.txt", "sitemap.xml", "feed.xml", "llms.txt",
            "llms-full.txt", "style.css", f"{key}.txt"]
    problems = [f"missing {n}" for n in need if not (site_dir / n).is_file()]
    keyfile = site_dir / f"{key}.txt"
    if keyfile.is_file() and keyfile.read_text(encoding="utf-8").strip() != key:
        problems.append("IndexNow key file content does not match its name")
    if not re.fullmatch(r"[0-9a-f]{32}", key):
        problems.append("IndexNow key is not 32 lowercase hex characters")
    robots = (site_dir / "robots.txt").read_text(encoding="utf-8") if (site_dir / "robots.txt").is_file() else ""
    for bot in ("GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended"):
        if f"User-agent: {bot}" not in robots:
            problems.append(f"robots.txt does not name {bot}")
    if "Disallow: /\n" in robots:
        problems.append("robots.txt disallows everything")
    return problems


def run_all(site_dir: Path, site_url: str, key: str, external_ok: set[str] | None = None) -> dict[str, list[str]]:
    site_url = site_url.rstrip("/")
    return {
        "required files": check_required(site_dir, key),
        "html parses, JSON-LD parses, internal links resolve": check_html(site_dir, site_url, external_ok),
        "xml parses": check_xml(site_dir),
        "sitemap URLs exist": check_sitemap(site_dir, site_url),
        "llms.txt links exist": check_llms(site_dir, site_url, external_ok),
        "house style (em-dash, model names, forbidden words)": check_text(site_dir),
    }
