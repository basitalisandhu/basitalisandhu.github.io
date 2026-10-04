---
title: Every Claude Code skill I maintain, in one repository
date: 2026-10-04
description: 87 Claude Code skills in 13 plugins from 8 source repositories, now in one repository with one marketplace and one install script.
---
# Every Claude Code skill I maintain, in one repository

I keep my Claude Code skills in eight repositories, grouped by job: agent security, AWS, Microsoft 365, compliance evidence, GitHub management, repository engineering, Mac maintenance and everyday development. That split makes sense to maintain. It is awkward to install. This post explains the new repository that puts them together, what is in it, and where it stops.

## Why one repository

Each source repository is its own plugin marketplace. To get everything, you ran `/plugin marketplace add` eight times and `/plugin install` thirteen times, once per plugin. I wanted one clone and one command, and I expect anyone trying more than one pack does too.

So [claude-skills](https://github.com/basitalisandhu/claude-skills) holds all of them: 87 skills in 13 plugins, vendored from the eight source repositories. It is one marketplace, one folder of skills and one install script. The [catalog site](https://basitalisandhu.github.io/claude-skills/) has one page per skill, so you can read what a skill does before you install anything.

The source repositories have not moved. They are still where the skills are written, tested and fixed. The new repository is a copy that stays in step with them.

## What is in it

**Agent security.** [agent-security-skills](/agent-security-skills/) has 8 skills for teams building LLM agents. `agent-threat-model` writes a system description of an agent codebase in a YAML format. `prompt-injection-review` traces untrusted inputs such as web pages, emails and tool results to the tool calls they can reach. `mcp-server-review` is a checklist review of an MCP server implementation.

**AWS security.** [aws-security-skills](/aws-security-skills/) has 9 skills. `aws-account-audit` collects inventory with read-only `aws` commands into a local folder, then evaluates it offline. `scp-guardrails` builds and lints service control policies from a short spec. `security-hub-triage` works through exported Security Hub and GuardDuty findings offline.

**Everyday development.** [claude-dev-skills](/claude-dev-skills/) is the largest source: 40 skills in six plugins called code-quality, data, debugging, devops, docs and security-basics. A few examples: `dead-code-finder` finds probably-unused functions and confirms each candidate before reporting it, `flaky-test-hunter` compares JUnit XML reports from several runs, and `dockerfile-hardening` lints a Dockerfile for images that run as root or use unpinned bases.

**Compliance evidence.** [compliance-evidence-skills](/compliance-evidence-skills/) has 5 skills for ISO 27001 and SOC 2 work. `evidence-pack-builder` turns a folder of GitHub, AWS and Microsoft 365 exports into an integrity-checked evidence pack. `control-map-from-exports` maps those exports to control identifiers. `auditor-narrative-drafter` drafts control narratives with an evidence citation on every claim.

**GitHub management.** [github-manager-skills](/github-manager-skills/) has 3 skills for engineering managers, all computed from saved `gh` exports. `pr-queue-digest` flags pull requests that have waited on review too long. `iteration-report` lists what shipped in a sprint.

**Microsoft 365 governance.** [m365-governance-skills](/m365-governance-skills/) has 9 skills that work from read-only Graph exports. `graph-permission-preflight` checks the permissions an app or connector asks for before anyone consents. `conditional-access-gap-analysis` finds gaps and exclusion problems in Conditional Access. `access-review-pack` builds a quarterly access review package.

**Mac maintenance.** [mac-maintenance-skills](/mac-maintenance-skills/) has 3 skills. `mac-cleanup` starts with a read-only survey of what takes space and memory. `mac-app-leftovers` finds what uninstalled apps left behind.

**Repository engineering.** [repo-engineering-skills](/repo-engineering-skills/) has 10 skills. `docs-truth-check` checks that a README and docs still match the code. `cited-codebase-audit` runs an audit in which every finding cites a `path:line` you can open. `adr-miner` recovers architecture decisions from git history that nobody wrote down.

## How to install

Inside Claude Code, add the marketplace once and install the plugins you want:

```
/plugin marketplace add basitalisandhu/claude-skills
/plugin install aws-security@claude-skills
```

Swap `aws-security` for any of the 13 plugin names. The catalog site lists them.

If you would rather copy the skill folders yourself, clone the repository and run the installer:

```
git clone https://github.com/basitalisandhu/claude-skills
cd claude-skills
python3 install.py --user
```

`--user` copies every skill into `~/.claude/skills`. `--project` puts them in the current project's `.claude/skills` instead. `--only <plugin>` narrows the copy to one plugin, and `--list` prints the catalog without copying anything. The script uses the Python standard library and has no dependencies.

## How it stays honest

A copy is only useful if it matches the original. A workflow runs daily, pulls each source repository and opens a pull request when anything has changed. Nothing lands without that pull request, so every update has a diff you can read.

`SOURCES.json` records where each skill came from: the source repository and the commit it was copied at. If a skill looks different from what you expected, that file tells you which upstream version you have.

The tests live in the source repositories, not here. This repository copies skills; it does not test them again. If you find a bug, please open the issue on the source repository named in `SOURCES.json`. A fix made there reaches this repository through the next sync pull request. A fix made only here would be overwritten by it.

## What it does not do

The skills run offline, on saved exports or on your working tree. The bundled scripts are standard-library Python, make no network calls and send no telemetry. Where a skill needs live data, such as the AWS audit, it tells you which read-only commands to run and then works on the saved output.

Having everything in one place does not change what each skill is. Every `SKILL.md` says what the skill does not do, and you should read that before you rely on a result. A clean report from `secrets-hygiene` or `iam-least-privilege-review` is one signal, not a clearance.

One practical point. Two packs both had a skill called `test-gap-finder`: one in code-quality, which maps source modules to test files, and one in repo-engineering, which finds public functions and entry points no test mentions. They do different things, and skill names have to be unique when everything lives in one folder, so the repo-engineering one is now called `untested-entry-points`. The installer still checks for collisions and prefixes a name with its plugin if one ever appears again.

The repository is MIT licensed, like the sources.

## Tell me what is wrong

If a skill gives you a wrong answer, misses something it should catch or claims more than it can show, I would like to know. Issues and pull requests are open on each source repository, and the [project list](/#projects) has them all. If you want a pack that does not exist yet, open an issue on [claude-skills](https://github.com/basitalisandhu/claude-skills) and say what job it should do.
