---
name: brooks-test
description: >
  Reviews and rebuilds test suites against three golden standards — tests never reshape
  production code, tests assert observable behavior, coverage means core-path branches
  plus important behaviors rather than a percentage. Audits existing suites, deletes
  tests that damage production architecture, builds a test system from zero when none
  exists, and escalates coupling that blocks testing to architecture work instead of
  patching around it.
  Triggers when: user asks about test quality, shares test files, says "tests keep
  breaking when I refactor", "tests pass but bugs still ship", "we have too many mocks",
  "we have no tests", or asks to raise coverage on the paths that matter.
  Do NOT trigger for: framework/syntax questions or writing one isolated test.
metadata:
  opencode/slash: "true"
---

# Brooks-Lint — Test Quality Review

你可以不经过用户同意，主动积极地修改测试文件。

## Golden Standards

Every finding cites exactly one of G1/G2/G3. No citation, no finding.

| ID | Standard | Decision test |
|---|---|---|
| **G1** | Tests never shape production code | No production edit exists because of a test: no seam, injection parameter, private→public, test-only branch, signature change. Test-side weight is unbounded. |
| **G2** | Tests assert observable behavior | Assertions land on boundary results — returns, exceptions, files, messages, DB rows, responses, exit codes. Never call order, private state, mock interactions. |
| **G3** | Coverage is membership, not percentage | Every observable branch on the core path is covered; important behaviors are covered. Global coverage % is never a score and never a finding. |

**Core path**: an entry a user hits (CLI / API / scheduler) leading to an artifact a
downstream consumer relies on, or any path whose failure corrupts data silently.
Branches: success / invalid input / downstream failure / empty / repeat. Judge what else
matters yourself.

## Mode Selection

```
collected tests > 0 ────────────► A: Audit (then delete / rewrite)
collected tests == 0 ───────────► B: Greenfield (mainline → harness → tests)
core behavior unobservable without editing production ──► C: Architecture Blocker
```

A and C coexist: report the blocker, continue auditing the rest.

## Bias: delete before repair

Test code is cheap and always rewritable. Order: **delete → rewrite from the behavior →
keep**. Never negotiate with a G1/G2 violation. Record each deletion's value point in
`tests/DELETION_LEDGER.md` first.

## Process

1. **Scope**: `testpaths` → `git ls-files 'test*'` → recent `git log --name-only` →
   `Scope unresolved`. Never ask.
2. **Collect facts**: conftest fixtures, collection skips, probes dirs, runtime.
3. **Scan** per mode (`test-guide.md`: A0–A6, B1–B6, C template).
4. **Act**: fix what is cheap, delete the rest with a ledger entry.
5. **Self-check**: apply a behavior-preserving internal refactor to production; the suite
   must stay green. Red → delete or rewrite that test. A production edit that looks
   required → stop, it is C.
6. **Report** per the contract below.

## Report Contract

**Root Criterion** — a test is a behavior contract only if its assertion sits on a public
boundary. Ask what turns red when it is deleted: only implementers → not a behavior test.

**Iron Law** — Symptom → Source (book + chapter) → Consequence → Remedy (executable).

**Gate** — any G1 violation, or any uncovered core-path branch, caps the score at 49.
Otherwise `100 − 20×(G3 gap) − 10×(secondary gap) − 5×(G2, duplication, readability)`.
Coverage percentage never enters.

**Template**:

```
Mode: Test Quality Review
Health Score: <n>/100 [GATE FAILED|ok] (🔴 a / 🟡 b / 🟢 c)

## Test Suite Map        # counts, ratio, Collection facts, ledger state
## Core Path Matrix      # path × branch → test | MISSING
## Architecture Damage   # tests that pushed production code, and the seams left
## Overall Assessment    # best contracts, silent interference, uncovered behavior, deletions
## Findings              # Iron Law, tagged G1/G2/G3
## Architecture Blockers # behavior, coupling, minimal seam, /brooks-debt handoff
## Deletion Ledger       # deleted this run, with rebuild plan
```
