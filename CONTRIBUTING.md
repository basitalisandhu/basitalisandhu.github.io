# Contributing

Thanks for helping. This repository is a personal site, so most changes come from the owner, but fixes are welcome.

## Good contributions

- A broken link, a typo or a rendering bug on a page.
- A README excerpt that renders badly: the fix usually belongs in `scripts/sync_repos.py` (what is extracted) or `sitekit/markdown.py` (how it renders), with a test.
- Accessibility, contrast or phone-layout problems.
- A check that would have caught a real mistake.

Corrections to a project's description belong in that project's repository; the daily sync picks them up.

## How

1. Fork and branch from `main`.
2. Make the change. If it touches the generator or the data, run:

   ```bash
   python3 -m pytest -q
   python3 build.py --check
   ```

   and commit the rebuilt `docs/` with your change; CI fails when `docs/` does not match a fresh build.
3. Open a pull request that says what changed and why.

## House style

Plain words, first person in posts, no em-dashes, no marketing adjectives, and no claim a repository cannot back with code or tests. The checks enforce part of this.

By contributing you agree that code is licensed MIT and post text CC BY 4.0, as described in [LICENSE](LICENSE), and you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
