#!/usr/bin/env python3
"""Build the site into docs/ from site.json, data/repos.json and content/*.md.

Offline and deterministic: the same inputs always produce the same bytes.

    python3 build.py                 # build into docs/
    python3 build.py --check         # build, then run the site checks
    python3 build.py --out /tmp/site --data tests/fixtures/repos.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from sitekit import checks, site  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "docs")
    ap.add_argument("--data", type=Path, default=ROOT / "data" / "repos.json")
    ap.add_argument("--content", type=Path, default=ROOT / "content")
    ap.add_argument("--check", action="store_true", help="run the site checks after building")
    args = ap.parse_args(argv)

    s = site.load_site(ROOT, args.data, args.content)
    css = (ROOT / "sitekit" / "style.css").read_text(encoding="utf-8")
    written = site.build(s, args.out, css)
    pages = [p for p in written if p.suffix == ".html"]
    print(f"built {len(written)} files ({len(pages)} HTML pages, {len(s.generated_repos())} project pages, "
          f"{len(s.posts)} posts) into {args.out}")
    if args.check:
        return report(args.out, s)
    return 0


def report(out: Path, s: site.Site) -> int:
    external = {r["own_site"] for r in s.repos if r.get("own_site")}
    results = checks.run_all(out, s.url, s.cfg["indexnow_key"], external)
    failed = 0
    for name, problems in results.items():
        print(f"{'ok  ' if not problems else 'FAIL'} {name}" + (f" ({len(problems)})" if problems else ""))
        for p in problems:
            print(f"     {p}")
        failed += len(problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
