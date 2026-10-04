# Security policy

This repository builds a static website. The site has no server-side code, no JavaScript, no forms, no cookies and no analytics. The build is standard-library Python that reads committed files; the only network access is `scripts/sync_repos.py`, which calls `api.github.com` read-only.

## Supported versions

Only the current `main` branch and the deployed site are supported.

## Reporting a vulnerability

Please do not open a public issue for a security problem.

1. Use GitHub's private vulnerability reporting on this repository ("Security" tab, "Report a vulnerability").
2. If that is unavailable, open an issue titled "Security contact request" with no details, and the maintainer will reply with a private channel.

You will get an acknowledgement within 5 working days and a fix or a mitigation plan within 30 days for confirmed issues.

## What counts

- Content from a synced README or description that reaches a page unescaped (HTML or script injection), or a link with a scheme other than http, https or mailto.
- A workflow that runs untrusted input, uses an unpinned action, or holds more permission than it needs.
- A token or secret written into `data/`, `docs/` or a log.

## What is public on purpose

`site.json` and `docs/<key>.txt` hold the IndexNow key. IndexNow keys are public by design: the key file must be served from the site so search engines can verify submissions. It is not a credential.
