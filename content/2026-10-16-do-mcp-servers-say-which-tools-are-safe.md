---
title: Do MCP servers say which tools are safe?
date: 2026-10-16
description: I read the tool registrations of 304 public MCP servers. Six in ten mark none of their tools as read-only or destructive, and only one delete-or-send tool in five says it is destructive.
---
# Do MCP servers say which tools are safe?

An MCP server can label each of its tools with four hints. `readOnlyHint` says the tool changes nothing. `destructiveHint` says it may delete or overwrite. `idempotentHint` says calling it twice does no more harm than calling it once, and `openWorldHint` says it reaches systems outside the server. A client uses these labels to decide when to stop and ask you before a call goes through.

When I published [the state of public agent skills and MCP servers](/posts/the-state-of-public-agent-skills-and-mcp-servers/) on Tuesday, this was the one question I could not answer. A server has to run before it will list its tools, I ran nothing, and only 10 repositories in the sample had a tool list committed to the repository. So this week I went back to the same sample and read the hints straight out of the servers' source code.

## The headline numbers

- **Six servers in ten mark nothing.** Of the 304 MCP servers whose tool registrations I could read, 188 (61.8%) annotate none of their tools. The 95% confidence interval runs from 56.3% to 67.1%. Only 69 of 304 (22.7%) annotate every tool.
- **About a third of tools carry a label.** 6,243 of the 17,688 tools (35.3%) set at least one hint. Tools cluster heavily by server, one repository alone holds more than 1,500, so the more honest figure is per server: the typical server labels 29.4% of its tools (95% CI 24.5% to 34.6%).
- **The tools that most need a label are no better.** 1,099 tools have a name that says delete, remove, drop, purge, send, pay, transfer, write or similar. 366 of them (33.3%) carry any hint, and 214 (19.5%) say `destructiveHint: true` outright. In 83 of the 117 repositories that ship such tools (70.9%), not one of them is labelled.
- **Read tools mostly do not say so either.** Of 7,609 tools named get, list, search, read and so on, 2,095 (27.5%) declare `readOnlyHint: true`.
- **Wrong labels are rare.** Only 7 of the 1,099 delete-or-send tools, in 3 of the 304 repositories, are marked read-only or non-destructive. The problem is silence, not lies.
- **Popularity barely helps.** 36 of 67 repositories with 100 or more stars set a hint somewhere in their source (53.7%), against 106 of 237 with fewer (44.7%). The intervals overlap.

The money names are the sharpest example. 42 tools are named for paying or charging, and none of them carries a single hint, though 34 of the 42 come from one repository.

## Why missing labels matter, and why they are not a vulnerability

The specification's defaults are cautious. A tool with no hints is assumed to be able to write, to be destructive and to talk to the outside world. A client that follows those defaults will still ask before it calls an unlabelled delete tool, so a missing hint does not, on its own, let anything happen silently.

The cost shows up somewhere else. When most tools carry no labels, a client cannot tell the 7,609 read-looking tools from the 1,099 delete-or-send ones. It can ask about everything, in which case people learn to approve prompts without reading them, or the user allows the whole server and the question is never asked again. Both outcomes are worse than a prompt that appears only when it should. That is the practical value of the hints: they let an honest server earn the right prompts.

They do not protect you from a dishonest server. A hint is a claim by the author, and the specification says clients should treat it as untrusted unless they trust the server. So the right reading of these numbers is about hygiene and usability, not about attacks.

## How I measured it

I took the 399 repositories in Tuesday's random sample that ship an MCP `server.json`, fetched each one's source at the exact commit recorded in the dataset, and read every tool registration statically for the main SDK styles in TypeScript, JavaScript, Python, Go, Rust and C#, without installing, building or running anything. Repository-level shares carry 95% Wilson intervals and tool-level shares carry intervals from resampling whole repositories, because one server can hold over a thousand tools. A random hand check of 60 tools found 59 real registrations, and for every one of those 59 the labelled or unlabelled verdict and the name class matched what I read in the source.

The full method, every rule, the hand-check file and the limitations are in the report page, [Do MCP servers say which tools are safe?](https://github.com/basitalisandhu/agent-skills-state-2026/blob/main/docs/mcp-tool-annotations.md), and the data is in [data/2026-10/annotations](https://github.com/basitalisandhu/agent-skills-state-2026/tree/main/data/2026-10/annotations): one row per tool, one row per repository, and a results file with every number and its interval. A test in the repository checks that every share on the report page matches that file.

## What to check before you install an MCP server

- **Open the tool definitions.** Search the source for `registerTool`, `server.tool`, `@mcp.tool`, `NewTool` or `McpServerTool` and look for `readOnlyHint` and `destructiveHint`. Six servers in ten have no label on any tool.
- **Read silence as "can change things".** That is what the defaults say and it is the only safe assumption.
- **Look for contradictions.** A tool whose name says delete, remove, send, pay or write should never be marked `readOnlyHint: true`, and a delete tool should not say `destructiveHint: false`.
- **Allow by name, not by server.** Put the read-only tools you trust on an allow list in your client and leave everything else on "ask". If you maintain a server, labelling your tools is what makes that possible for your users.
- **Pin the version.** Tuesday's report found that 46.0% of local MCP configurations start a server with no pinned version. A label you checked last week means little if the package can change under you.

If you maintain a server, [mcp-tools-lint](/mcp-tools-lint/) checks a server's tool list for missing annotations and for a delete-named tool marked read-only, and runs as a GitHub Action.

## What the data does not show

It reads source code, not running servers. A hint added at run time, by middleware or by a framework default is missed, and so is any registration style I did not write a pattern for: 73 repositories had source but no registration I recognised, and they sit outside the denominator. Tool names are a weak signal of behaviour, which is why I write "named for deleting", not "deletes". A few very large servers dominate the pooled tool counts, so the repository-level numbers deserve more weight. And this is a subset of a sample of what GitHub code search surfaces, not a census of every MCP server.

## The data

Everything is in [basitalisandhu/agent-skills-state-2026](https://github.com/basitalisandhu/agent-skills-state-2026), now at version 1.1.0, under CC BY 4.0 for the data and MIT for the scripts. Nothing in Tuesday's report changed. If a number looks wrong to you, or you know a registration style I missed, an issue is the best way to tell me.
