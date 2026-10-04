#!/usr/bin/env python3
"""Run the site checks over an already built docs/ (or --out DIR) without rebuilding."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build  # noqa: E402
from sitekit import site  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "docs")
    args = ap.parse_args(argv)
    return build.report(args.out, site.load_site(ROOT))


if __name__ == "__main__":
    sys.exit(main())
