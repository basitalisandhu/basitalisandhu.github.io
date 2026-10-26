---
title: What do skills that ask for the whole shell do with it?
date: 2026-10-26
description: I read 3,715 public agent skills that grant unscoped Bash. Three in ten never show a shell command, most of the rest need three commands or fewer, and a third install, delete, push or eval.
---
# What do skills that ask for the whole shell do with it?

A skill's `allowed-tools` line is a permission slip. While the skill is active, whatever it lists runs without the host asking you first. Write `Bash(git status:*)` and the agent can check the branch; anything else still prompts. Write a bare `Bash`, or `Bash(*)`, and the agent can run any command at all, with no prompt in between.

Two weeks ago, [the state of public agent skills and MCP servers](/posts/the-state-of-public-agent-skills-and-mcp-servers/) found that 407 of 2,621 repositories with skills (15.5%) give at least one skill that unscoped grant, 10,073 declarations in all. That number says the door is open. This week I went through it and asked what is on the other side: when a skill asks for the whole shell, which commands does it actually show you, does it need more than a handful of them, and how often does it download, delete, push, escalate or read credentials?

## The headline numbers

- **Three in ten never use the shell they ask for.** 1,109 of the 3,715 skills I read (29.9%) show no shell command anywhere in their `SKILL.md` and ship no script. The 95% confidence interval runs from 26.3% to 33.5%. Counting each distinct skill text once, so that copies do not count twice, it is 25.6%. For these skills, removing `Bash` from `allowed-tools` loses nothing the page asks for.
- **Most of the rest need three commands or fewer.** Of the 2,545 skills that do show shell commands, 1,418 (55.7%) use three or fewer distinct commands, and 806 (31.7%) use exactly one. Three `Bash(command:*)` rules would cover everything those skills document, and the host would keep prompting for anything else.
- **A third do something worth reading first.** 1,289 of 3,715 skills (34.7%) document or ship at least one of nine riskier behaviours, and 279 of the 392 repositories (71.2%) contain at least one such skill. The common ones are ordinary developer work: installing or fetching a package (15.7%), a direct HTTP call (14.4%), recursive deletion or discarding git work (9.2%), and running a built string through `eval` (8.4%).
- **The rarer ones are the ones that matter.** 186 skills (5.0%) push or publish (`git push`, `gh pr create`, `npm publish`). 74 (2.0%) pipe a download straight into a shell, the familiar `curl ... | bash`. 61 (1.6%) use `sudo` or open up file permissions, 50 (1.3%) read a credential store or a `.env` file, and 16 (0.4%) change the machine beyond the project: cron jobs, launch agents, shell start-up files, global git config.
- **It is mostly on the page.** Only 647 skills (17.4%) ship a script at all. Of the 1,289 with a riskier behaviour, 1,154 show it in the `SKILL.md` commands the agent is told to run; just 135 hide it only in a bundled script.
- **Stars do not help.** In repositories with 100 or more stars, 27 of 44 (61.4%) have such a skill, against 252 of 348 (72.4%) for the rest; the intervals overlap.

## Why an unscoped grant matters, and why it is not an accusation

None of this says any skill is malicious. Most of what I found is ordinary developer work. The point is about where the checkpoint sits.

With a scoped grant, the host stays in the loop for everything the skill did not say it needed. With an unscoped one, the only review a command ever gets is whatever you did before you installed the skill. That matters more than it sounds, because a skill does not only follow its own text. It reads web pages, issues and files in your repository, and any of those can carry instructions. An unscoped grant turns a prompt injection that reaches the skill into shell access, with nobody asked.

For three skills in ten the grant buys nothing the page uses. For more than half of the rest, three rules would do. Narrowing the grant costs the author one line.

## How I measured it

I took the 407 repositories in the October sample that grant unscoped Bash and kept the 400 with the smallest hash of a fixed seed and the repository name, to stay under the study's ceiling for re-fetching. For each, I fetched the commit recorded in the dataset, read every `SKILL.md` (up to 2,000 a repository), and for up to 20 skills with an unscoped grant fetched the files bundled in the skill's folder. The fetch downloads files by their git object id and writes them out directly, so no checkout, hook or filter ever runs. 393 repositories were still available. Nothing was installed, built or run.

A short standard-library script reads the commands each `SKILL.md` asks the agent to run, from shell code blocks and from inline code that starts with a known command. Each command's first word, after wrappers like `sudo`, is its head; the number of distinct heads is the number of scoped rules the skill would need. Nine rule families then run over those commands and over the bundled scripts, ignoring text that is only printed.

Skill-level intervals come from resampling whole repositories; repository-level ones are Wilson intervals. I read 60 skills drawn at random against their pages and scripts: all 60 grant unscoped Bash, the "shows a command or ships a script" label matched in all 60, the three-or-fewer class matched in all 33 with commands, and 17 of the 20 behaviour flags were right. I found two misses, both in one skill.

The full method, all nine rules, the hand-check file and the limitations are on the report page, [What do skills that ask for the whole shell do with it?](https://github.com/basitalisandhu/agent-skills-state-2026/blob/main/docs/skills-with-unscoped-bash.md). The data is in [data/2026-10/skill-bash](https://github.com/basitalisandhu/agent-skills-state-2026/tree/main/data/2026-10/skill-bash): one row per skill, one row per repository, and a results file with every number and its interval. A test checks that every share on the report page matches that file.

## What to check before you install a skill that asks for Bash

- **Find the grant.** Open the `SKILL.md` and read `allowed-tools`. A bare `Bash` or `Bash(*)` means any command, no prompt.
- **Look for commands.** If the page has no shell blocks and the skill ships no scripts, which is three skills in ten, delete `Bash` from your copy.
- **Scope what is there.** List the first word of each command. More than half of these skills use three or fewer; replace the grant with `Bash(git status:*)`, `Bash(python scripts/run.py:*)` and so on.
- **Search for the sharp edges.** `curl` or `wget` piped into a shell, `sudo`, `rm -rf`, `git reset --hard`, `git push --force`, `git push`, `gh pr create`, `npm publish`, `pip install`, `npx`, `uvx`, `eval`, reads of `~/.ssh`, `~/.aws`, a keychain or `.env`, and writes to `crontab`, launch agents or `~/.zshrc`.
- **Read the scripts it calls, wherever they live.** Plenty of skills run tools from a plugin's shared folder or your home directory. The grant covers them too, and this study did not read them.
- **Pin what it installs.** A package the skill runs through `npx` or `uvx` is part of the skill; give it a version.
- **Re-read after updates.** An unscoped grant lets tomorrow's new command run without asking.

If you publish skills, [skill-scan-gate](/skill-scan-gate/) flags unscoped Bash grants in CI, the rule that produced the first report's 15.5%, and the [skill review pack in claude-code-tooling-skills](/claude-code-tooling-skills/) walks through reviewing a third-party skill before you install it.

## What the data does not show

It reads the page, not the run: an agent with unscoped Bash can run commands its page never mentions, and five of the 26 hand-checked skills with no command still describe shell work in prose or hand off to a workflow file elsewhere. Scripts outside the skill's folder were not fetched, so the script-level shares are a lower bound. Rule fixes made during the hand check make its figures somewhat optimistic, which is why the rarer categories deserve the most care. And this is a slice of a sample of what GitHub code search surfaces, not a census.

## The data

Everything is in [basitalisandhu/agent-skills-state-2026](https://github.com/basitalisandhu/agent-skills-state-2026), now at version 1.3.0, under CC BY 4.0 for the data and MIT for the scripts. No number in the first report or the earlier follow-ups changed. If a number here looks wrong, or you know a pattern I missed, an issue is the best way to tell me.
