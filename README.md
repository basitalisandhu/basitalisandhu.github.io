# basitalisandhu.github.io

Source of [basitalisandhu.github.io](https://basitalisandhu.github.io/): a small docs hub for the open-source repositories of [Muhammad Basit Ali](https://github.com/basitalisandhu), covering AI agent security, MCP tooling, Claude Code skill packs and cloud security automation. It has one page per repository (what it is, how to install it, links to releases, packages and issues), the latest releases, posts, an RSS feed, a sitemap and `llms.txt`.

No framework, no JavaScript, no analytics, no external assets. A standard-library Python generator turns committed data into static HTML in `docs/`, and GitHub Actions deploys `docs/` to Pages.

## Layout

| Path | What it is |
|---|---|
| `build.py` | The generator. `python3 build.py` writes `docs/`; `--check` also runs the site checks. Offline and deterministic. |
| `site.json` | Site URL, author, bio, description and the IndexNow key. |
| `data/repos.json` | Every listed repository: description, one-liner, theme, topics, language, licence, the README's first screen, an install block and the last five releases. Written by `scripts/sync_repos.py`, committed so the build needs no network. |
| `data/exclude.json` | Repository names to leave off the site (empty by default). |
| `content/*.md` | Posts. |
| `sitekit/` | The Markdown converter, the page renderer, the stylesheet and the checks. |
| `scripts/sync_repos.py` | Refreshes `data/repos.json` from the GitHub API. |
| `scripts/check_site.py` | Runs the checks over an existing `docs/` without rebuilding. |
| `scripts/changed_urls.py` | Lists the page URLs that changed between two commits, for IndexNow. |
| `docs/` | The built site. Committed; CI fails if it does not match a fresh build. |

## Build and check locally

```bash
python3 build.py --check          # build docs/ and run every check
python3 -m pytest -q              # converter, generator and check tests
```

Python 3.11 or newer. Nothing to install for the build; the tests need `pytest`.

The checks: every HTML page parses with balanced tags, a doctype and a title; every JSON-LD block parses and has `@context` and `@type`; internal links and anchors resolve; `sitemap.xml` and `feed.xml` parse and every sitemap URL is a built file; every link in `llms.txt` is a page on this site (or a repository's own Pages site); `robots.txt` allows everyone, AI crawlers by name; the IndexNow key file matches `site.json`; and no generated file contains an em-dash, an AI model name or a word on the house blocklist.

## Add a post

1. Create `content/YYYY-MM-DD-your-slug.md`:

   ```markdown
   ---
   title: Your title
   date: 2026-10-12
   description: One sentence for the post list, the feed and search results.
   ---

   First paragraph.

   ## A section

   Text, `code`, **bold**, [links](/agent-threat-model/), lists and fenced code blocks.
   ```

   The slug is the file name without the date (`slug:` in the front matter overrides it). A leading `# Heading` in the body is used as the title when `title:` is absent. The converter supports headings, paragraphs, lists, block quotes, fenced code, inline code, bold, emphasis and links; images and raw HTML are dropped or escaped on purpose.
2. Run `python3 build.py --check` and commit the post together with the rebuilt `docs/`.
3. Push to `main` (or open a pull request). The `pages` workflow deploys and pings IndexNow with the changed URLs.

## How the sync works

`scripts/sync_repos.py` lists the owner's public repositories through the GitHub API and keeps those that are not forks, not archived, and not the profile, `.github` or this site's repository (plus anything in `data/exclude.json`). For each one it records the description, topics, language and licence, the README's first screen (from the title to the first `##` heading, minus badges, images, raw HTML and tables, with relative links made absolute), the most useful code block under an Install, Quick start, demo or Usage heading, and the last five releases. Themes and one-liners come from the tables in the [profile README](https://github.com/basitalisandhu/basitalisandhu); a repository not in those tables gets a theme from its topics and the first clause of its description.

A repository with its own GitHub Pages site (for example `ai-agent-incidents`) owns the path `/<name>/` on this host, so the site links to that instead of generating a page that would be shadowed.

The `sync` workflow runs daily: it syncs, rebuilds, runs the checks and, when anything changed, opens or updates a pull request from the `sync/repos-data` branch. Pull requests opened with the workflow token do not start other workflows; the sync job already ran the build and the checks, and closing and reopening the pull request runs `ci` as well.

To run it by hand (a token is optional and only raises the rate limit):

```bash
GITHUB_TOKEN="$(gh auth token)" python3 scripts/sync_repos.py
python3 build.py --check
```

## Workflows

- `ci.yml` (pull requests): lint, tests, build, checks, and a diff that fails if `docs/` is stale.
- `pages.yml` (push to `main`): the same, then `actions/deploy-pages`, then the `indexnow-ping` action from [security-actions](https://github.com/basitalisandhu/security-actions) with the changed URLs.
- `sync.yml` (daily): refresh the data and open a pull request.

Every action is pinned to a full commit SHA; Dependabot proposes updates weekly.

## Licence

Code (the generator, scripts, tests, stylesheet and workflows) is MIT, see [LICENSE](LICENSE). Posts in `content/` and their rendered pages are [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Repository descriptions and README excerpts in `data/` and `docs/` belong to their repositories and carry those repositories' licences.
