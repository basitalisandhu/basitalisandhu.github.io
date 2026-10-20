---
title: Do MCP server READMEs tell you which version to run?
date: 2026-10-20
description: I read the install commands in the READMEs of 264 public MCP servers. 95.5% never name an exact version, and a quarter ask for the latest release on every launch.
---
# Do MCP server READMEs tell you which version to run?

Almost nobody installs a local MCP server from first principles. You open the repository, scroll to the snippet for your client, and paste something like `"command": "npx", "args": ["-y", "some-server"]` into a config file. From then on, whatever that line names is the code your agent starts every session, with your permissions and usually with an API token in its environment.

Last week, [the state of public agent skills and MCP servers](/posts/the-state-of-public-agent-skills-and-mcp-servers/) found that 159 of 346 repositories (46.0%) that commit a local MCP configuration start at least one server with no pinned version. That is the downstream picture. This week I went upstream, to the snippet people copy, and asked a narrower question: when an MCP server's own README tells you how to launch it, does it name a version?

## The headline numbers

- **READMEs almost never name a version.** Of the 264 MCP server repositories whose READMEs contain a launch command, 252 (95.5%) never pin an exact version in any of them. The 95% confidence interval runs from 92.2% to 97.4%. Only 12 of 264 (4.5%) show an exact version even once.
- **The version is right there, in another file.** 212 of these repositories ship a `server.json`, the manifest the official MCP Registry reads, and it records an exact version of their own package. In 202 of those 212 (95.3%), the README's commands for that same package never mention a version. The maintainer knows which release is current; the copy-paste line just leaves it out.
- **A quarter ask for the newest release on every start.** 69 of 264 repositories (26.1%) use an explicit moving tag such as `@latest`, `:latest` or `uvx --refresh`. Those commands fetch whatever was published most recently each time the client launches, with nothing in between to review it.
- **Most npx lines also skip the prompt.** Of 576 `npx` commands, 410 (71.2%) pass `-y`, which answers yes to npx's question before it installs a package it has not seen before.
- **No ecosystem and no popularity band is better.** For npm, 188 of 189 repositories show a floating command; for PyPI, 66 of 69; for container images, 53 of 55. Repositories with 100 or more stars never pin in 65 of 69 cases (94.2%), against 187 of 195 (95.9%) for the rest.
- **Proxies too.** All 17 repositories that tell you to run the `mcp-remote` proxy leave its version open.

Counted by command rather than by repository, 817 of the 835 distinct launch commands I found (97.8%) float.

## Why an unpinned line matters, and why it is not a vulnerability

A floating launch command hands the choice of what code runs to the package registry, on the day you start the client. If a maintainer's account is taken over, or a release ships a bug or a quietly changed tool, everyone on a floating command picks it up on their next restart. In a normal application build, a lockfile stands between you and that. In an MCP client config, the README line is often the only thing there.

Not every floating line is equally loose. A bare `npx -y some-server` or `uvx some-server` runs whichever version your machine cached first, and does not update itself later, so it is a lottery about the day you installed, and two colleagues following the same README can run different code. A moving tag like `@latest` is the opposite: it re-resolves on every launch, so a release reaches you within hours of publication. Neither is a pin, which is why I report the moving-tag share on its own.

None of this says any package is malicious. It is a default. The README is the template, people copy the template, and the 46.0% of unpinned configurations in last week's report is what that template looks like once it lands in other people's repositories. The fix is cheap and sits with the maintainer: print the exact version in the README and bump it at release time, as the 12 repositories that already do show. The MCP project's own quickstart and example pages use the unpinned form too, which is what [issue #3431](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/3431) on the specification repository is about.

## How I measured it

I took the 399 repositories in last week's random sample that ship an MCP `server.json`, the same set as [the tool annotations report](/posts/do-mcp-servers-say-which-tools-are-safe/), and fetched only their README and `server.json` files at the exact commits recorded in the dataset. 391 were still available. Nothing was installed, built or run.

A short standard-library script reads the root README and the README next to each `server.json`, and finds commands that fetch a published package or image and run it: `npx`, `bunx`, `pnpm dlx`, `yarn dlx`, `uvx`, `uv tool run`, `pipx run` and `docker run`, in client configs (JSON, TOML and YAML), in shell lines and in inline code. Prose that merely mentions npx does not count, and neither do development tools such as the MCP Inspector, test runners or scaffolders, local paths, placeholders like `pkg@<version>` or images the same README builds locally. Each command's version is classed as exact, a range, a moving tag or absent.

Repository-level shares carry 95% Wilson intervals. Command-level shares carry intervals from resampling whole repositories, because one monorepo alone holds 116 commands. I read 60 commands drawn at random against their READMEs: all 60 were real instructions to fetch and run a published package, 56 of the 60 start the MCP server itself (the other four are a driver setup step, an installer and an unrelated command-line tool, all still unpinned), and the version class matched my reading in all 60.

The full method, every rule, the hand-check file and the limitations are on the report page, [Do MCP server READMEs tell you which version to run?](https://github.com/basitalisandhu/agent-skills-state-2026/blob/main/docs/mcp-readme-install-pins.md). The data is in [data/2026-10/readme-pins](https://github.com/basitalisandhu/agent-skills-state-2026/tree/main/data/2026-10/readme-pins): one row per command, one row per repository, and a results file with every number and its interval. A test checks that every share on the report page matches that file.

## What to check before you install an MCP server

- **Find the version first.** Look at the repository's `server.json`, its registry page or its latest release, then write that version into your config: `npx -y some-server@1.4.2`, `uvx some-server==0.9.1`, or `docker run -i --rm some/image@sha256:...` with the image digest. Nineteen READMEs in twenty will not do this for you.
- **Read moving tags as auto-update.** `@latest`, `:latest`, `uvx --refresh`, `npx --prefer-online` and `docker run --pull always` mean "install last night's release every time the client starts".
- **A bare name is not a pin.** No version means whatever your cache holds, or the newest release on a fresh machine.
- **Keep `-y` for packages you chose.** It skips the only prompt npx gives you.
- **Pin the plumbing.** Proxies such as `mcp-remote` run every session too.
- **Know what a pin does not cover.** An exact version fixes the top-level package, not its dependencies. For a server you rely on, a lockfile, an image digest or a recorded hash of the tool list is the stronger check.
- **Upgrade on purpose.** Read the changelog, change the pin, restart.

If you keep MCP configs in a repository, [skill-scan-gate](/skill-scan-gate/) flags unpinned servers in committed configs in CI, the same rule family last week's report used.

## What the data does not show

It reads READMEs, not documentation sites, so a project that pins in its docs but not its README is counted as floating. It is static pattern matching, so a command built from variables or written in a form I did not anticipate is missed; the hand check bounds what was found, not what was missed. Monorepos with many READMEs weigh heavily in the command counts, which is why the repository-level shares are the ones to quote. And this is a subset of a sample of what GitHub code search surfaces, not a census.

## The data

Everything is in [basitalisandhu/agent-skills-state-2026](https://github.com/basitalisandhu/agent-skills-state-2026), now at version 1.2.0, under CC BY 4.0 for the data and MIT for the scripts. No number in the first report or the tool annotations report changed. If a number here looks wrong, or you know a launch form I missed, an issue is the best way to tell me.
