---
title: What the OWASP Agentic Top 10 maps to in 88 real incidents
date: 2026-10-16
description: 88 public AI incidents coded against the OWASP Agentic Top 10: which categories show up, what they travel with, and what the list leaves out.
---
# What the OWASP Agentic Top 10 maps to in 88 real incidents

When a team asks me which agent risks to plan for, the [OWASP Top 10 for Agentic Applications for 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) is the list I point them to first. It is a good list. But a list of categories does not tell you which ones you will actually meet, what they look like on the ground, or what sits outside the list altogether.

So I counted. The [ai-agent-incidents](https://github.com/basitalisandhu/ai-agent-incidents) dataset I maintain has 88 publicly documented events from February 2023 to September 2026: 29 incidents, 48 vulnerability disclosures and 11 threat reports. Each one is coded from its primary source under a [written codebook](https://github.com/basitalisandhu/ai-agent-incidents/blob/main/docs/codebook.md), and each carries a mapping to the ten `ASI` categories where the source supports one. This week I added a script that cross-tabulates those mappings against the other coded fields. Every number below comes from it.

## How to reproduce the numbers

The script is standard-library Python, reads the committed JSON records and needs no network:

```console
$ git clone https://github.com/basitalisandhu/ai-agent-incidents
$ cd ai-agent-incidents
$ python3 scripts/agentic_crosstab.py --stdout
## Coverage

- Events: **88** (2023-02 to 2026-09)
- Mapped to at least one ASI category: **57** (64.8%)
- Mapped to none: **31** (35.2%)
- Mapped events with two or more categories: **26** of 57 (45.6%)

| lens | events | mapped | unmapped | mapped share |
|---|---:|---:|---:|---:|
| `surface` | 51 | 46 | 5 | 90.2% |
| `target` | 21 | 7 | 14 | 33.3% |
| `weapon` | 16 | 4 | 12 | 25.0% |
...
```

The full output is committed as [docs/owasp-agentic-crosstab.md](https://github.com/basitalisandhu/ai-agent-incidents/blob/main/docs/owasp-agentic-crosstab.md), and a test fails if it drifts from the records. The per-category counts across the ten categories are: ASI01 Agent Goal Hijack 26, ASI05 Unexpected Code Execution 17, ASI02 Tool Misuse and Exploitation 16, ASI04 Agentic Supply Chain Vulnerabilities 12, ASI03 Identity and Privilege Abuse 7, ASI10 Rogue Agents 5, ASI06 Memory and Context Poisoning 4, ASI07 Insecure Inter-Agent Communication 1, and ASI08 Cascading Agent Failures and ASI09 Human-Agent Trust Exploitation none.

## Six things the cross-tab shows

**1. The list covers AI as an attack surface, and not much else.** The dataset codes every event by the role AI plays: a *surface* (the agent is a path to someone else's assets), a *target* (the AI's own data, prompts, keys or serving stack are attacked) or a *weapon* (an attacker uses AI against people or systems). 46 of the 51 surface events (90.2%) map to at least one ASI category. Only 7 of 21 target events and 4 of 16 weapon events do. Of the 31 events that map to nothing, 26 are target or weapon events: exposed databases behind AI products, leaked API tokens, attacks on model-serving software, deepfake fraud and AI-orchestrated intrusion campaigns.

That is not a flaw in the list. It says what it is for. If your threat model only uses the Agentic Top 10, it will cover the agent you build and miss the stack it runs on and the attackers who now use the same tools. 85 of the 88 events map to at least one of the three frameworks the dataset uses (the OWASP LLM Top 10 and MITRE ATLAS are the other two), so use them together.

**2. Goal hijack is the front door, and it comes in through content.** ASI01 is the largest category at 26 events, and 25 of those 26 are coded as indirect prompt injection. The content arrived through a web page in 9, a document in 6, a repository issue or pull request in 4, and email and support tickets in 2 each. Nobody typed the attack into the chat box; the agent read it while doing its job.

**3. "Read-only" did not keep data in.** 12 of the 26 goal hijack events involve an agent coded with read-only authority. In 10 of those 12 the outcome was data exfiltration, and in 9 the data left through an image or link fetch: the agent was told to render a URL with the data in its query string, and the client fetched it. If your approval for an agent rests on "it can only read", ask what it can render and what it can fetch.

**4. Categories travel together.** 26 of the 57 mapped events (45.6%) carry two or more categories. The common pairs are ASI01 with ASI02 (9 events) and ASI01 with ASI05 (6). In practice goal hijack is the start of the chain and tool misuse or code execution is where the harm happens. I find it more useful to put controls at the consequence end, on what a hijacked agent can call and run, than to rely on spotting every injection.

**5. Unexpected code execution means a shell.** All 17 ASI05 events involve an agent coded with shell or code execution authority, and 16 ended in code execution. Across the whole dataset, 38 of 88 events involve that authority, more than any other. A coding agent with a terminal is the single most represented kind of agent in the public record.

**6. Identity abuse is under-reported, not rare.** ASI03 has only 7 events, though 5 events involve an agent holding cloud credentials and 5 involve repository write access. Only one of the cloud-credential events and one of the repository-write events is mapped to ASI03. My reading is that public write-ups describe the injection and the payload, and rarely the identity the agent ran as or how broad its grants were, so the mapping cannot be made with confidence. The blast radius was still set by those grants. I wrote about that gap in [Agent identities are the new service accounts](/posts/agent-identities-are-the-new-service-accounts/), and [agent-off-switch](/agent-off-switch/) is the tool I use to list and stop those identities.

## The empty columns

Two categories have no events at all, and a third has one. ASI08 Cascading Agent Failures and ASI09 Human-Agent Trust Exploitation are at zero, and ASI07 Insecure Inter-Agent Communication at one.

An empty column in a sample of public reports is not evidence that a risk is rare. 48 of the 88 events are vulnerability disclosures, and a disclosure usually describes one bug in one product with a clean proof of concept. A failure that cascades across several agents, or an agent that talks a human approver into clicking yes, is harder to show in one advisory and harder to attribute in an incident report. These may be the categories most likely to be under-counted rather than the least likely to happen.

ASI10 Rogue Agents is the opposite case. Its 5 events are all incidents, not disclosures, and 4 of them are coded as autonomous operations: evaluation and research agents that went outside their intended scope, breached systems they were not meant to touch or published data they should not have. These are recent: the year table shows how mapping coverage moved from 4 of 11 events in 2023 and 5 of 13 in 2024 to 24 of 32 in both 2025 and 2026, as agents with real tools became the subject of most reports.

## What I take from it for a threat model

For an agent I am reviewing, the counts suggest an order of work:

1. **Treat every input the agent reads as untrusted**, not just chat. Web pages, documents, issues, pull requests, tickets and email are where ASI01 came in.
2. **Control egress, including link and image rendering.** That one channel carried 9 of the 26 hijack events out.
3. **Constrain what a hijacked agent can call and run.** Tool allowlists, scoped shell access and sandboxing address ASI02 and ASI05, the categories that most often follow ASI01.
4. **Size the identity before the pilot starts.** The record will not tell you how often ASI03 happens, because write-ups rarely describe the grants. Assume it applies.
5. **Pin what the agent loads.** ASI04 events came in through packages in 7 of 12 cases. My [study of 2,999 public skill and MCP repositories](/posts/the-state-of-public-agent-skills-and-mcp-servers/) found 46.0% of repositories that configure a local MCP server start at least one with no pinned version, and [skill-scan-gate](/skill-scan-gate/) fails a pull request that adds one.
6. **Then add the target and weapon lenses**, with the OWASP LLM Top 10, MITRE ATLAS and ordinary application security.

[agent-threat-model](/agent-threat-model/) turns a YAML description of the agent into a ranked threat register and control checklist, offline and in CI, and every threat it reports carries its OWASP Agentic, OWASP LLM and ATLAS ids.

## What the data cannot tell you

- **It is a convenience sample.** It holds what vendors, researchers and journalists chose to publish. No share in this post estimates how common anything is in the world; it describes 88 records.
- **The mappings are one maintainer's reading.** Lens and vector were blind-coded twice for the paper behind the seed data (kappa 0.82 and 0.87 with the second coder). The OWASP mappings were not, and an empty mapping means "no confident mapping", not "none applies".
- **Dates are the month of the public report**, not of the event.
- **Small cells are small.** ASI06, ASI07 and ASI10 rest on one to five events each; read them as examples, not trends.

Each record links its primary source, so any count here can be checked against the events behind it. Corrections and new events are welcome as [issues or pull requests](https://github.com/basitalisandhu/ai-agent-incidents/blob/main/CONTRIBUTING.md); a new event needs a public primary source.
