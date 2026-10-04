---
title: Four open repositories for securing AI agents, and what each is for
date: 2026-10-05
description: A map of the open tools for AI agent security: an incident dataset, Semgrep rules for agent code, a threat-model CLI and Claude Code skill packs, with where each one stops.
---
# Four open repositories for securing AI agents, and what each is for

Teams are putting language models in front of tools, data and credentials faster than they are writing down what could go wrong. I have spent the year building small, open tools for that gap and for the cloud accounts the agents run in. This post is the map: what each repository is for, where it stops, and the order I would use them in.

None of it is a platform. Each repository stands alone, links its siblings, and does one job. The [project list on this site](/#projects) and the profile at [github.com/basitalisandhu](https://github.com/basitalisandhu) are the index.

## 1. Start from evidence: ai-agent-incidents

Arguments about agent risk are usually made from a handful of famous cases. [ai-agent-incidents](https://github.com/basitalisandhu/ai-agent-incidents) (browse it at [its own site](https://basitalisandhu.github.io/ai-agent-incidents/)) is a structured dataset of publicly documented AI agent and LLM security incidents from February 2023 onwards, one record per event.

Each record was coded from a primary source under a written codebook: the role AI played (weapon, target or surface), the vector, the input channel, the authority the agent held, the output channel and the outcome. Each is mapped to the OWASP Top 10 for LLM Applications, the OWASP Top 10 for Agentic Applications and MITRE ATLAS. There are JSON and CSV downloads, an RSS feed and a searchable site. The data is CC BY 4.0.

Its limit matters as much as its content. It is a convenience sample of what vendors and researchers chose to disclose, so it over-represents some kinds of incident, and no percentage computed from it estimates how common anything is. An empty mapping means no confident mapping, not that no category applies. If you disagree with a coding, the codebook is in the repository and a pull request is welcome.

## 2. Check the code: agentic-semgrep-rules

Some agent vulnerabilities come down to one short function: model output reaching a shell, a query, a URL fetch or `eval`. [agentic-semgrep-rules](/agentic-semgrep-rules/) is a set of Semgrep rules for AI agent code in Python, TypeScript and JavaScript. They look for model output reaching exec, shells, SQL, URLs, files and HTML, user input in system prompts, over-broad tools, MCP servers without authentication, leaked keys and unsafe model loading, and each rule maps to a CWE and the OWASP lists.

Every rule has tests, so a change to a rule shows up as a failing test rather than a surprise in someone else's pipeline. Tests show what a rule flags; they do not show what it misses. A clean run is one signal, not a clearance, and a false positive is a bug worth reporting.

## 3. Model the system: agent-threat-model

Code scanning finds lines. It does not tell you what an agent can reach if it is tricked. [agent-threat-model](/agent-threat-model/) takes a YAML description of the system (the model, its tools, where its inputs come from, what credentials it holds, who approves what) and produces a ranked threat register under STRIDE and the OWASP Agentic Top 10, a Mermaid diagram, a control checklist, a residual risk score and SARIF for GitHub code scanning.

It runs offline, as a CLI or a GitHub Action, with no model in the loop, so the same description always produces the same output and you can diff a threat model between two pull requests. It only knows what you tell it; the YAML is as good as your description of the system.

## 4. Bring it into the editor and the account: the skill packs

The same habits are packaged as Claude Code skills, each with tested scripts that run offline on saved output rather than on a live system:

- [agent-security-skills](/agent-security-skills/): threat modelling, configuration audits, prompt injection review, MCP server review and incident lookup for securing LLM agents.
- [aws-security-skills](/aws-security-skills/): a read-only AWS account audit, SCP guardrails, IAM least-privilege review and Security Hub and GuardDuty triage.
- [repo-engineering-skills](/repo-engineering-skills/): README and documentation claims checked against the code, audits where every finding cites a resolvable `path:line`.
- [m365-governance-skills](/m365-governance-skills/): Graph permission preflight, Entra ID posture review, Intune baseline check and a quarterly access review pack, from read-only exports.

## How I would use them together

1. Read a few records from the dataset that look like your architecture.
2. Describe your agent in YAML and run the threat-model CLI; compare its register against those records.
3. Run the Semgrep rules over the agent's code, and fix or consciously accept each finding.
4. Put the threat model and the rules in CI so they are still true next quarter.

## What is not here

These tools do not stop an agent from doing anything at runtime. They help you find, describe and review risk before it ships. I would rather say that plainly than imply more.

## What is next

One repository a week. The Show HN sequence runs through the incident dataset, the Semgrep rules and the threat-model CLI; the skill packs and the other developer tooling follow. If you run agents against real systems, I would like to hear what these tools miss. Issues and pull requests are open on every repository, and [the project list](/#projects) has them all.
