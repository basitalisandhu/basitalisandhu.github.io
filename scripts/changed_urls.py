#!/usr/bin/env python3
"""Print the site URLs whose built page changed between two commits, one per line.

Used after a deploy to tell IndexNow what to recrawl. docs/ is committed, so a
git diff of docs/ is exactly the set of changed pages (removed pages included,
so engines drop them). With no base commit (first push) every page is listed.

    python3 scripts/changed_urls.py --base HEAD^ --head HEAD
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def to_url(site_url: str, rel: str) -> str | None:
    """docs/a/index.html -> https://host/a/ ; non-page files and 404.html -> None."""
    rel = rel.removeprefix("docs/")
    if not rel.endswith(".html") or rel == "404.html":
        return None
    if rel == "index.html":
        return site_url + "/"
    if rel.endswith("/index.html"):
        return f"{site_url}/{rel[: -len('index.html')]}"
    return f"{site_url}/{rel}"


def changed_files(base: str, head: str) -> list[str]:
    ok = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"], cwd=ROOT, capture_output=True)
    if ok.returncode != 0:
        out = subprocess.run(["git", "ls-files", "docs"], cwd=ROOT, capture_output=True, text=True, check=True)
    else:
        out = subprocess.run(["git", "diff", "--name-only", base, head, "--", "docs"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [line for line in out.stdout.splitlines() if line]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="HEAD^")
    ap.add_argument("--head", default="HEAD")
    args = ap.parse_args(argv)
    site_url = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))["url"].rstrip("/")
    urls = sorted({u for f in changed_files(args.base, args.head) if (u := to_url(site_url, f))})
    print("\n".join(urls))
    return 0


if __name__ == "__main__":
    sys.exit(main())
