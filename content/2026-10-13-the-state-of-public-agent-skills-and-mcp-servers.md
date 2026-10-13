---
title: The state of public agent skills and MCP servers
date: 2026-10-13
description: A random sample of 2,999 public repositories that ship agent skills, plugins or MCP servers, scanned and hand-checked. Five findings, with denominators, and what to check before you install one.
---
# The state of public agent skills and MCP servers

Agent skills, plugin marketplaces and MCP servers are now installed the way browser extensions once were. Someone finds a repository, copies a line into a config file, and the agent gains new instructions, new shell access or a new process that starts with every session. I wanted to know what that supply looks like on the ground, measured rather than guessed.

So on 13 October 2026 I took a random sample of 2,999 public GitHub repositories that ship a `SKILL.md`, a plugin or marketplace manifest, or an MCP `server.json`. I fetched only the agent configuration files, ran nothing, scanned them with open-source tools and checked the scanners by hand before trusting any number. The dataset, method, scripts and charts are in [agent-skills-state-2026](https://github.com/basitalisandhu/agent-skills-state-2026), with the data under CC BY 4.0.

## What the sample is

The repositories came from GitHub code search: 31 queries split by file size, which surfaced 7,456 distinct non-fork repositories. I drew 3,000 at random and one failed to download. The result is young and mostly small: 2,512 of the 2,999 were created in 2026 and the median repository has 4 stars, though 434 have 100 or more. 2,621 contain at least one skill, 336,285 `SKILL.md` files in all. 373 have an agent hook configuration and 346 configure at least one MCP server that runs as a local process.

Every share below has its own denominator, because a pinning finding only makes sense for repositories that configure an MCP server, and a skill finding only for repositories with skills.

## Five findings

**1. Most repositories give no way to report a vulnerability.** 2,459 of 2,999 (82.0%) have no `SECURITY.md`. Popularity barely helps: among the 434 repositories with 100 or more stars it is still 75.6%. If you find a problem in a skill you depend on, there is usually no stated route to tell the author privately.

**2. Nearly half of MCP configurations run code that can change under you.** Of the 346 repositories that configure a local MCP server, 159 (46.0%) start at least one with no pinned version. 100 (28.9%) run an npm package through `npx` with no exact version, 63 (18.2%) ask for the `latest` tag outright, and 38 (11.0%) run a Python package without a version. Each session start can fetch whatever the package owner, or anyone who takes over the package, published last. The 100-plus star band is the worst for this, at 57.8%, though on only 45 repositories.

**3. A third ship with no licence.** 982 of 2,999 (32.7%) have no licence file at the root. For zero-star repositories it is 53.7% (of 984); for repositories with 100 or more stars, 16.6% (of 434). Without a licence, a team has no clear right to copy a skill into its own repository, which is how most skills end up being used.

**4. One in six skill repositories gives a skill the whole shell.** 407 of the 2,621 repositories with skills (15.5%) declare at least one skill whose `allowed-tools` grants `Bash` with no command scoping, 10,073 declarations in total. That is not proof of misuse. It does remove the host's chance to ask before each command.

**5. One in eight skill repositories has a skill whose header does not parse.** In 330 of 2,621 (12.6%) at least one `SKILL.md` has YAML front matter that a standard parser rejects, usually because a description contains an unquoted colon. That is 4,761 of 336,285 files (1.4%). A host that cannot read a skill's name and description cannot decide when to load it, and nothing tells the author.

Two smaller results. Of the 373 repositories with hook configurations, 13 have a hook that by default calls a host other than the local machine; I read every flagged hook by hand to get that number. And 146 of 2,621 skill repositories have a description over 1,024 characters, a common host limit.

## How far to trust the scanners

I did not report a measure until I had checked how often it was right. Unrestricted Bash was right in 10 of 10 sampled findings, unpinned MCP servers in 19 of 22, and YAML failures in 10 of 10. The licence and security-policy checks agreed with GitHub's own detection for 99% and 98% of findings.

Some measures did not survive. The linter's "no Use when sentence" check was right only 5 times in 12, because most descriptions it flagged did say when to use the skill, in other words or another language, so I dropped it. The secret rules were the weakest of all: a check for provider tokens was right 0 times in 10, mostly because the hits were scanner regexes, placeholders and example responses in documentation.

That matters for anyone counting "leaked secrets" in public skill repositories. The secret-shaped-string rules fired in 471 of the 2,999. After triaging every hit by structure, without displaying any value, 30 possible live credentials in 17 repositories remained. Those were reported privately to their owners before this post went out, and neither the post nor the dataset names them.

## What to do before installing a skill or MCP server

- **Pin every MCP server.** Write `package@1.2.3`, never a bare name or `@latest`, and update on purpose. It is the most common finding that can run new code without review, and it is a one-line fix.
- **Read `allowed-tools`.** A skill that asks for unscoped `Bash` should say why, or be scoped to the commands it needs.
- **Read the hook scripts, not only the manifest.** Hooks run on every tool call. Most I read stay local, but some phone home on install or post session data to a webhook.
- **Check the licence before copying a skill** into your own repository.
- **Lint your own skills in CI.** A colon in a description is enough to stop a host reading the header, and it is cheap to catch.
- **Treat a scanner's secret count as a reading list,** not a result.
- **Give the agent its own identity and know how to switch it off.** Pinning and scoping limit what a skill can do; the identity it runs as limits the damage when one goes wrong. I wrote about that in [Agent identities are the new service accounts](/posts/agent-identities-are-the-new-service-accounts/).

## What the data does not show

It does not show that any repository is malicious or that any finding was exploited. It measures the presence of patterns at one commit on the default branch, statically, without running a skill, a hook or a server. It describes what GitHub code search surfaces, which leans towards young, small, personal projects; a curated marketplace may look better. Some precision samples are small, between 5 and 12 findings, and none of them say anything about what the scanners miss. "Fails YAML parsing" means one strict parser rejects it; an agent host may be more lenient.

It is also a snapshot. Search results change daily, so a rerun of the scripts draws a different sample. The method is what reproduces, and the repository has everything needed to run it again.

## The data

The repository [basitalisandhu/agent-skills-state-2026](https://github.com/basitalisandhu/agent-skills-state-2026) has one row per repository in CSV and JSON, the precision table, the chart data, the full method and the scripts, with a citation file if you want to reference it. Corrections are welcome as issues.
