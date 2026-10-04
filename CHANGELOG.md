# Changelog

All notable changes to this site and its generator. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - 2026-10-05

### Added

- Standard-library generator (`build.py`, `sitekit/`) with a small Markdown converter, writing `docs/`: home page (bio, four themed project tables, latest releases, packages link, posts), one page per repository with `SoftwareSourceCode` JSON-LD, posts with `BlogPosting` JSON-LD, posts index, `404.html`, `sitemap.xml`, `robots.txt` (AI crawlers allowed by name), RSS `feed.xml` for posts and releases, `llms.txt`, `llms-full.txt`, `.nojekyll` and the IndexNow key file.
- `scripts/sync_repos.py`: refreshes `data/repos.json` from the GitHub API and the profile README.
- Site checks: HTML well-formedness, JSON-LD, internal links and anchors, sitemap and llms.txt targets, robots.txt, IndexNow key, and house style (no em-dashes, no model names, blocklisted words).
- Workflows: `ci` on pull requests, `pages` deploy with an IndexNow ping of changed URLs, daily `sync` pull request. Actions pinned by SHA; Dependabot for actions.
- First post: "Four open repositories for securing AI agents, and what each is for".
