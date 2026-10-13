---
title: Agent identities are the new service accounts
date: 2026-10-13
description: AI agents run as app registrations, IAM roles and GitHub Apps that nobody owns or reviews. The failure modes, the controls, and an offline tool for them.
---
# Agent identities are the new service accounts

Part of my job is running access reviews. Human accounts are the easy part: there is an HR system, a manager, a leaver process. The hard part has always been the service accounts, and AI agents have made that part bigger.

An agent does not act with its own authority. It acts with whatever identity it was given. In practice that is an Entra app registration or service principal, a managed identity, an AWS IAM role or an access key, a GitHub App installation or a deploy key. These are the service accounts we already struggle to govern, and agents add more of them, created faster, often by a team running a pilot rather than by the people who run identity.

The pattern I keep seeing has three parts. Nobody owns the list. Nobody recertifies it. And when something goes wrong, nobody can stop one of these identities quickly and prove it is stopped.

## Why this is an identity problem, not a model problem

The [OWASP Top 10 for Agentic Applications for 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) lists ASI03, Identity & Privilege Abuse, as its own category. The [OWASP announcement](https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/) describes leaked credentials letting agents operate "far beyond their intended scope". Whatever an agent is tricked into doing, the blast radius is set by its identity's grants.

Microsoft says much the same in its [governance guidance for agent identities](https://learn.microsoft.com/en-us/entra/id-governance/agent-id-governance-overview): agents have historically reached Microsoft services through tools that use service principals. [Microsoft Entra Agent ID](https://learn.microsoft.com/en-us/entra/agent-id/what-is-microsoft-entra-agent-id) is its answer, a dedicated identity type for agents built from agent identity blueprints, with Conditional Access, Identity Protection, governance and audit logs extended to them. It is a good direction. It does not cover the AWS role your coding agent assumes or the GitHub App it pushes with, and many agents in Entra still run as ordinary app registrations.

## The failure modes I look for

These are the patterns I look for first in a review.

- **An ownerless identity with a tenant-wide Graph application permission.** An application permission such as `Mail.ReadWrite` works for every mailbox in the tenant with no signed-in user. If nobody owns the app registration, nobody will notice when it is misused, and nobody will answer the question "do we still need this?".
- **A role with `Action: "*"` that a CI agent assumes through OIDC.** Federation is the right way to give a pipeline credentials. But an OIDC trust to a role with `*` on `*` means any workflow that can satisfy the trust condition has the whole account.
- **A credential older than 90 days.** A client secret or access key that has not been rotated is a long-lived secret sitting in a pipeline variable, a vault or a laptop. AWS's [IAM security best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html) say to require workloads to use temporary credentials with IAM roles, and to update access keys where long-term credentials cannot be avoided.
- **An owner who left.** The identity had an owner when it was created. That person moved on, the owner field was cleared or now points at a disabled account, and the identity kept working.
- **A GitHub App with administration write on every repository.** Administration covers settings, branch protection and deletion. GitHub's [best practices for creating a GitHub App](https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/best-practices-for-creating-a-github-app) start with selecting the minimum permissions the app needs. Read-write deploy keys are a smaller version of the same problem: GitHub's [deploy key documentation](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys) notes that they have no expiry date and are tied to the repository, not to a user.
- **Stopping a role does not end existing sessions.** Changing an IAM role's trust policy stops new sessions. Credentials already issued stay valid until they expire. AWS documents how to [revoke role sessions](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_revoke-sessions.html) with an `AWSRevokeOlderSessions` policy keyed on `aws:TokenIssueTime`. If your off switch is "edit the trust policy", it is half a switch.

## The controls

None of these controls is new. They are the service account controls, applied to a population that grew while nobody was counting.

1. **Inventory.** One list of every non-human identity across Microsoft 365, AWS and GitHub, with the likely agents marked.
2. **Owner.** A named person or team for each one. No owner, no access.
3. **Least privilege.** Grants sized to the task, not to the pilot. AWS points to IAM Access Analyzer to generate policies from access activity, and GitHub to minimum permissions and limiting the repositories an app can reach.
4. **Credential hygiene.** No secrets where a federated or managed credential will do; rotation and an age limit where a secret is unavoidable; expired credentials deleted.
5. **Recertification.** On a schedule, the owner confirms the identity is still needed and its grants are still right. AWS's best practices include regularly reviewing and removing unused users, roles, permissions and credentials.
6. **An off switch.** A tested, ordered procedure to stop one identity: disable it, end live sessions, remove grants and credentials, and check the audit log.
7. **Drift in CI.** New identities, new grants and lost owners between reviews should fail a check until a person accepts them.

## How agent-off-switch maps to those controls

I built [agent-off-switch](https://github.com/basitalisandhu/agent-off-switch) (`aos`) for the reviews I run. It reads saved exports from Entra, AWS and GitHub, plus an optional `agents.csv` register, and works offline with no credentials of its own. Everything below is real output from the synthetic demo tenant that ships in the repository: the ids are fake and the AWS account is the documentation account `111122223333`.

**Inventory, owner, least privilege and credential hygiene** come from `aos review`, which ranks findings by blast radius (0 to 100) and gives each a fix:

```console
$ aos review examples/demo-tenant --as-of 2026-10-09
# Agent access review

As of 2026-10-09: 13 non-human identities, 11 look like agents. 15 findings (8 error), ranked by blast radius (0 to 100, see docs/scoring.md).

## 4 agent identities nobody owns

- **coding-agent-runner** `aws-role:coding-agent-runner` (blast radius 100): Action * on Resource *
  - switch off: `aos off examples/demo-tenant aws-role:coding-agent-runner`
- **repo-autopilot** `github-app:repo-autopilot` (blast radius 95): administration: write on every repository (settings, branch protection, deletion)
  - switch off: `aos off examples/demo-tenant github-app:repo-autopilot`
- **mail-triage-agent** `entra:aaaaaaaa-0000-4000-8000-000000000001` (blast radius 90): Mail.ReadWrite as an application permission changes data for every user in the tenant
  - switch off: `aos off examples/demo-tenant entra:aaaaaaaa-0000-4000-8000-000000000001`
...
```

The findings table that follows covers the rest of the failure modes above, including a client secret 434 days old and a deploy key that can push, each with its fix.

The same review can be written as SARIF for GitHub code scanning. `aos inventory` gives the full table of identities with owners, credentials, grants and last use, as Markdown, CSV or JSON.

**The off switch** is `aos off`. It prints an ordered runbook and runs nothing. For the coding agent's role, the first two steps are the point I made above: stop new sessions, then revoke the ones already issued.

```console
$ aos off examples/demo-tenant aws-role:coding-agent-runner --as-of 2026-10-09
# Off-switch runbook: coding-agent-runner

Identity `aws-role:coding-agent-runner` (aws-iam-role on aws). Owners: none recorded. Blast radius 100. Exports as of 2026-10-09.

aos printed these commands and ran none of them. Run each change in order, then its verification, and keep the verification output for the incident record. Values in <angle brackets> are for you to fill in.

## 1 disable

### Step 1: Stop new sessions: replace the trust policy (now trusts Federated: arn:aws:iam::111122223333:oidc-provider/token.actions.githubusercontent.com) with a deny-all one; save the current one first
...
## 2 revoke sessions and grants

### Step 2: Revoke every session issued before the disable time (the console's Revoke active sessions)
...
## 5 verify with the audit log

### Step 5: Confirm in CloudTrail that nothing succeeded after the disable time
...
## Coverage

Every credential and grant in the exports is named by a step.
```

Each step in the full output has a change command, a verification command and a line to record the time and the person. The coverage line matters: if a grant in the exports is not named by any step, `aos` says so and exits 1.

**Drift in CI** is `aos drift`, which compares a saved inventory with today's exports:

```console
$ aos drift examples/drift/baseline.json examples/demo-tenant --as-of 2026-10-09 --accept examples/drift/accepted.txt
# Agent identity drift

From 2026-09-01 (11 identities) to 2026-10-09 (13 identities): 4 changes, 3 not reviewed.

| Change | Identity | Detail | Reviewed |
|---|---|---|---|
| new-identity | `github-app:repo-autopilot` | repo-autopilot (github-app, no owner, blast radius 95) | **no** |
| new-identity | `github-app:docs-preview-bot` | docs-preview-bot (github-app, web-team@example.com, blast radius 55) | yes |
| new-grant | `aws-role:coding-agent-runner` | agent-all (score 100) | **no** |
| owner-lost | `entra:aaaaaaaa-0000-4000-8000-000000000001` | was owned by messaging-team@example.com; now no owner | **no** |
...
```

It exits 1 while anything is unreviewed, so it can gate a pull request. Accepting a change means adding its key to the accept file, so the decision sits in version control next to the inventory.

## What it does not do

I would rather say this plainly.

- **Recertification is supported, not performed.** `aos` gives you the data a recertification needs: owners, grants, credential ages, last use, and the unused and no-owner findings. It does not send attestations, collect decisions or remove access when nobody answers. That is still a process you run, or a governance product's job.
- **It never changes anything.** It calls no cloud API and runs no command. `off` prints commands for a person to run.
- **It is not real time.** It sees what the exports saw. An identity created after the export is invisible until the next run.
- **It does not read every limit on access.** Azure role assignments, AWS permission boundaries, service control policies, resource policies, Exchange RBAC for Applications scopes and Conditional Access are not read, so a score can overstate reach that one of those limits.
- **An owner who left is only partly covered.** `drift` flags an owner that disappears between two inventories. It does not check whether a named owner's account is still active.
- **It does not judge GitHub App activity** (the installations export has no last-use date) **or look inside agents**: prompts, tool calls and memory are out of scope.
- **It does not replace Entra Agent ID**, an identity governance product or a cloud security platform. It gives you one offline list across platforms and a way to act on it.

## Where to start

If you run access reviews, add the agent identities to the next one. Take the read-only exports, list what exists, and put a name against every row. The ones nobody claims are your first off-switch drill.

The repository is at [github.com/basitalisandhu/agent-off-switch](https://github.com/basitalisandhu/agent-off-switch), with the demo tenant, the [threat model](https://github.com/basitalisandhu/agent-off-switch/blob/main/docs/threat-model.md) and the [scoring rules](https://github.com/basitalisandhu/agent-off-switch/blob/main/docs/scoring.md). Issues and pull requests are welcome, especially new export formats and corrections to the scoring.
