#!/usr/bin/env python3
"""Refresh data/repos.json from the GitHub API, so the site build can stay offline.

For every public, non-fork, non-archived repository of the owner (minus the
profile repository, .github and this site) it records the description, topics,
language, licence, the README's first screen, an install block, the last five
releases and whether the repository has its own Pages site. Themes and
one-liners come from the tables in the profile README.

    GITHUB_TOKEN=... python3 scripts/sync_repos.py            # writes data/repos.json if it changed
    python3 scripts/sync_repos.py --meta-dir ../repos-meta     # also restrict to repos with a public meta file
    python3 scripts/sync_repos.py --check                      # exit 1 if the file would change

A token is optional (unauthenticated calls work, at a lower rate limit). It is
read from GITHUB_TOKEN or GH_TOKEN and only sent to api.github.com.
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.github.com"
FALLBACK_THEMES = ["Claude Code skill packs", "MCP tooling", "Security tooling", "Data and lists"]
INSTALL_HEADINGS = re.compile(r"quick ?start|\bdemo\b|getting started|install|usage", re.I)
EM_DASH = "\u2014"


class GitHub:
    def __init__(self, token: str | None) -> None:
        self.token = token

    def get(self, path: str, raw: bool = False):
        req = urllib.request.Request(API + path)
        req.add_header("Accept", "application/vnd.github.raw" if raw else "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        req.add_header("User-Agent", "basitalisandhu.github.io-sync")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (fixed https host)
            body = resp.read().decode("utf-8")
        return body if raw else json.loads(body)

    def try_get(self, path: str, raw: bool = False):
        try:
            return self.get(path, raw)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise


# ---------------------------------------------------------------- text helpers

def clean(text: str) -> str:
    """House style for imported text: no em-dashes."""
    return re.sub(rf"\s*{EM_DASH}\s*", ", ", text or "").strip()


def absolutise_links(text: str, html_url: str, branch: str) -> str:
    def fix(m: re.Match) -> str:
        target = m.group(2)
        if re.match(r"^(https?:|mailto:)", target):
            return m.group(0)
        if target.startswith("#"):
            return f"{m.group(1)}({html_url}{target})"
        return f"{m.group(1)}({html_url}/blob/{branch}/{target.removeprefix('./')})"
    return re.sub(r"(\[[^\]]*\])\(([^)\s]+)\)", fix, text)


def _is_badge_or_noise(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if s.startswith(("<", "|", "[!")) or "<!--" in s:
        return True
    stripped = re.sub(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)|!\[[^\]]*\]\([^)]*\)", "", s)
    return not stripped.strip()


def readme_intro(readme: str, html_url: str, branch: str, limit: int = 2200) -> str:
    """Markdown of the README's first screen: everything between the H1 and the first H2,
    minus badges, images, raw HTML and tables, with links made absolute."""
    lines = readme.replace("\r\n", "\n").split("\n")
    start = next((i + 1 for i, line in enumerate(lines) if line.startswith("# ")), 0)
    body: list[str] = []
    in_fence = False
    for line in lines[start:]:
        if line.strip().startswith("```"):
            in_fence = not in_fence
        if not in_fence and line.startswith("## "):
            break
        if not in_fence and _is_badge_or_noise(line):
            continue
        body.append(line)
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(body)).strip()
    if len(text) > limit:  # keep whole paragraphs up to the limit
        kept, total = [], 0
        for block in text.split("\n\n"):
            if total + len(block) > limit and kept:
                break
            kept.append(block)
            total += len(block) + 2
        text = "\n\n".join(kept)
    return clean(absolutise_links(text, html_url, branch))


def readme_install(readme: str, max_lines: int = 16) -> dict | None:
    """The most useful fenced code block under an Install / Quick start / demo / Usage heading.

    Shell blocks win over YAML, YAML over anything else (an .npmrc or a JSON config is
    rarely the first thing a reader needs); within a rank, the first block in the README wins.
    """
    shell = {"bash", "sh", "shell", "console", "zsh", "text", ""}
    best: tuple[int, int, str, str, str] | None = None
    order = 0
    for section in re.split(r"(?m)^## +", readme)[1:]:
        heading = section.split("\n", 1)[0]
        if not INSTALL_HEADINGS.search(heading):
            continue
        for m in re.finditer(r"(?ms)^```([\w+-]*)[ \t]*\n(.*?)^```", section):
            lang, code = m.group(1).lower(), m.group(2)
            looks_like_config = code.lstrip().startswith(("@", "//", "{", "["))
            rank = 0 if lang in shell and not looks_like_config else 1 if lang in ("yaml", "yml") else 2
            order += 1
            if best is None or (rank, order) < best[:2]:
                best = (rank, order, lang, code, heading)
    if best is None or best[0] == 2:
        return None
    _, _, lang, code_text, heading = best
    code = code_text.rstrip("\n").split("\n")
    if len(code) > max_lines:
        code = code[:max_lines] + ["# ... see the README for the rest"]
    code = [re.sub(r"\s+# see .* below\s*$", "", line) for line in code]  # README-internal pointers
    return {"lang": lang or "bash", "code": clean("\n".join(code)), "from": clean(heading.strip())}


def profile_themes(readme: str, owner: str) -> tuple[list[dict], dict[str, str]]:
    """Themes (H2 sections with two-column repo tables) and one-liners from the profile README."""
    themes: list[dict] = []
    one_liners: dict[str, str] = {}
    current: dict | None = None
    row = re.compile(rf"^\|\s*\[([\w.-]+)\]\(https://github\.com/{re.escape(owner)}/[\w.-]+/?\)\s*\|(.*)\|\s*$")
    for line in readme.splitlines():
        if line.startswith("## "):
            current = {"title": clean(line[3:].strip()), "repos": []}
            themes.append(current)
            continue
        if line.startswith("#"):
            current = None
            continue
        m = row.match(line)
        if m and current is not None and m.group(2).count("|") == 0:
            name, text = m.group(1), clean(m.group(2).strip())
            current["repos"].append(name)
            one_liners[name] = text
    return [t for t in themes if t["repos"]], one_liners


def short_line(description: str) -> str:
    """A one-liner for a repo the profile README does not list: the part before the first colon."""
    head = description.split(": ", 1)[0].strip().rstrip(".")
    return f"{head}." if 20 <= len(head) < len(description) else description


def fallback_theme(repo: dict) -> str:
    topics = set(repo.get("topics") or [])
    name = repo["name"]
    if topics & {"claude-code-plugin", "agent-skills"} and name.endswith("skills"):
        return "Claude Code skill packs"
    if topics & {"dataset", "awesome-list", "open-data"}:
        return "Data and lists"
    if name.startswith("mcp-") or "mcp-server" in topics or "model-context-protocol" in topics:
        return "MCP tooling"
    return "Security tooling"


# ---------------------------------------------------------------- sync

def list_repos(gh: GitHub, owner: str) -> list[dict]:
    out, page = [], 1
    while True:
        batch = gh.get(f"/users/{owner}/repos?per_page=100&type=owner&sort=full_name&page={page}")
        out += batch
        if len(batch) < 100:
            return out
        page += 1


def releases(gh: GitHub, owner: str, name: str) -> list[dict]:
    rels = gh.try_get(f"/repos/{owner}/{name}/releases?per_page=10") or []
    rows = [
        {"tag": r["tag_name"], "name": clean(r.get("name") or r["tag_name"]), "date": (r.get("published_at") or r["created_at"])[:10],
         "url": r["html_url"]}
        for r in rels if not r.get("draft")
    ]
    rows.sort(key=lambda r: (r["date"], r["tag"]), reverse=True)
    return rows[:5]


def sync(gh: GitHub, owner: str, previous: dict, meta_dir: Path | None, exclude: set[str]) -> dict:
    prev_by_name = {r["name"]: r for r in previous.get("repos", [])}
    meta: dict[str, dict] = {}
    if meta_dir:
        for f in meta_dir.glob("*.json"):
            m = json.loads(f.read_text(encoding="utf-8"))
            if m.get("visibility") == "public" and m.get("name"):
                meta[m["name"]] = m

    profile = gh.try_get(f"/repos/{owner}/{owner}/readme", raw=True)
    if profile:
        themes, one_liners = profile_themes(profile, owner)
    else:
        themes = previous.get("themes", [])
        one_liners = {r["name"]: r["one_liner"] for r in previous.get("repos", [])}

    skip = {owner, ".github", f"{owner}.github.io"} | exclude
    repos = []
    for r in list_repos(gh, owner):
        name = r["name"]
        if r.get("fork") or r.get("archived") or r.get("private") or r.get("visibility", "public") != "public" or name in skip:
            continue
        if meta_dir and name not in meta:
            continue
        branch = r.get("default_branch") or "main"
        html_url = r["html_url"]
        readme = gh.try_get(f"/repos/{owner}/{name}/readme", raw=True)
        prev = prev_by_name.get(name, {})
        description = clean(r.get("description") or meta.get(name, {}).get("description") or "")
        entry = {
            "name": name,
            "description": description,
            "one_liner": one_liners.get(name) or short_line(description),
            "theme": "",
            "topics": sorted(r.get("topics") or meta.get(name, {}).get("topics") or []),
            "language": r.get("language") or "",
            "license": ((r.get("license") or {}).get("spdx_id")) or "",
            "html_url": html_url,
            "default_branch": branch,
            "homepage": r.get("homepage") or "",
            "own_site": f"https://{owner}.github.io/{name}/" if r.get("has_pages") else None,
            "intro_md": readme_intro(readme, html_url, branch) if readme else prev.get("intro_md", ""),
            "install": readme_install(readme) if readme else prev.get("install"),
            "releases": releases(gh, owner, name),
        }
        repos.append(entry)
    repos.sort(key=lambda x: x["name"])

    names = {r["name"] for r in repos}
    themes = [{"title": t["title"], "repos": [n for n in t["repos"] if n in names]} for t in themes]
    themes = [t for t in themes if t["repos"]]
    if not themes:
        themes = [{"title": t, "repos": []} for t in FALLBACK_THEMES]
    by_title = {t["title"]: t for t in themes}
    placed = {n for t in themes for n in t["repos"]}
    for r in repos:
        if r["name"] not in placed:
            title = fallback_theme(r)
            by_title.setdefault(title, {"title": title, "repos": []})
            if by_title[title] not in themes:
                themes.append(by_title[title])
            by_title[title]["repos"].append(r["name"])
    for t in themes:
        for n in t["repos"]:
            next(r for r in repos if r["name"] == n)["theme"] = t["title"]
    return {"owner": owner, "themes": themes, "repos": repos}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--owner", default="basitalisandhu")
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "repos.json")
    ap.add_argument("--meta-dir", type=Path, help="only include repos with a public JSON meta file here")
    ap.add_argument("--exclude", type=Path, default=ROOT / "data" / "exclude.json",
                    help="JSON list of repository names to leave off the site")
    ap.add_argument("--check", action="store_true", help="exit 1 if the data would change; write nothing")
    args = ap.parse_args(argv)

    previous = json.loads(args.out.read_text(encoding="utf-8")) if args.out.is_file() else {}
    exclude = set(json.loads(args.exclude.read_text(encoding="utf-8"))) if args.exclude.is_file() else set()
    gh = GitHub(os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
    data = sync(gh, args.owner, previous, args.meta_dir, exclude)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    old = args.out.read_text(encoding="utf-8") if args.out.is_file() else ""
    changed = text != old
    print(f"{len(data['repos'])} repositories, {sum(len(r['releases']) for r in data['repos'])} releases: "
          f"{'changed' if changed else 'unchanged'}")
    if args.check:
        return 1 if changed else 0
    if changed:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
