# Test Guide — detailed scans

Load after `SKILL.md`. Nothing here overrides the golden standards.

## Collection Facts

```
testpaths:        <pyproject / pytest.ini / setup.cfg>
conftest:         <path, fixtures shared across how many files>
collection skips: <importorskip / skipif / markers>  → zero-collection tests, not coverage
probes/:          <exists? gitignored?>
runtime:          <full suite seconds, or "unknown">
ledger:           <tests/DELETION_LEDGER.md exists? entries?>
```

```bash
git ls-files 'test*' 'tests/*' 'spec/*'
grep -rn "testpaths" pyproject.toml pytest.ini setup.cfg 2>/dev/null
git log --since=90.days --name-only --pretty=format: | sort | uniq -c | sort -rn | head -20
```

Never ask for scope. If every inference path is empty, emit `Scope unresolved` and give
structural advice from the source tree only.

---

## A. Audit Mode

### A0. Architecture Damage (G1) — delete aggressively

Find tests that changed the shape of production code:

- Production symbols existing only for tests: `test`, `_for_test`, `TESTING` in the name,
  or zero references outside tests.
- Parameters / defaults only tests pass.
- Private symbol made public with tests as the sole consumer.
- Interfaces with one implementation, created to be substituted.
- `conftest.py` patching production attributes (`monkeypatch.setattr`, `mock.patch`).
- Tests importing production internals; production importing test helpers.

```bash
grep -rn "for test\|test_only\|_for_test\|TESTING" <src>
grep -rn "monkeypatch.setattr\|mock.patch" tests/conftest.py
```

Delete every test whose only reason to exist is the artificial seam, and log it. If it
covers a core-path branch, rewrite it through the real entry first. Never delete
production code here — record the seam as a blocker for `/brooks-debt`.

A test that removes zero core-path coverage is deleted without further analysis. "It might
catch something" is not a reason to keep it.

### A1. Obscurity (G2)

Read 5–10 names cold: each must state subject + scenario + expected. Flag invisible
external state, one massive `setUp` inherited by everything, failures that cannot say
which behavior broke.

### A2. Brittleness (G2)

Names with "and"; 3+ unrelated assertions; assertions on call order, intermediate values,
private attributes. Name the refactor each one would block.

### A3. Mock Abuse (G2)

Sample 3–5 tests once for A2+A3. Signals: mock setup longer than assertions;
`assert_called*` as the primary assertion; >3 mocks in one test; production methods
callable only from tests.

**Not a finding**: fakes at process boundaries — clock, network, filesystem, subprocess,
third-party API, cloud SDK. The name (fake / stub / spy / mock) is irrelevant; only G1–G3
adjudicate. If a collaborator cannot be substituted without editing production, drive the
test through the nearest real entry; if impossible, it is `C`.

### A4. Duplication

Count instances (10+ 🔴, 3–9 🟡, 1–2 🟢). Only real duplication counts: extraction would
create shared mutable state or a fixture everyone inherits; identical input/assertion
pairs; the same scenario asserted at unit, integration and E2E with no layer difference.

Independent-but-identical setup is intentional, not a finding. One function + many input
sets + one assertion = good parameterization. Different inputs taking different branches
= several contracts in one name; split.

### A5. Core Path Coverage (G3)

Build the matrix before judging:

```
core path         branch              test
entry → artifact  success             test_x.py::test_y
entry → artifact  invalid input       MISSING
```

- `MISSING` = 🔴 G3 and gates the score.
- Assert side effects (DB rows, messages, files), not only returns. Return-only coverage
  of a core path is 🟡.
- Legacy module under modification with no tests: require a characterization test before
  the change, asserting current behavior even if wrong.

A 70/20/10 ratio is diagnostic only, never a target or a finding. One integration test
through a real entry beating three mock-collaborator unit tests is normal. Runtime >10 min
is 🟡, and reaches 🔴 only alongside missing core coverage.

### A6. Lifecycle Debt (G3)

Zombie tests (zero collected) and environment-coupled tests in the permanent suite: 🔴 —
they advertise coverage that does not exist. Golden files without an `UPDATE_*` entry
point: 🟡. Scratch probes: move to a gitignored `probes/` or delete and log.

### A7. Output

Fill the template, run the self-check, add one line: suite green / N deleted / M rewritten.

---

## B. Greenfield Mode

The harness places the outside world on the test side once, so every later test is
additive with zero marginal risk to production. That is why the standard is high here.

1. **Find the mainline.** From an entry point (`__main__`, console script, HTTP route,
   cron config) follow the code to the artifact it produces. Take exactly one path — the
   one the product cannot run without. Do not enumerate modules.
2. **Stand the boundary up.** One substitute per external edge (clock, net, fs,
   subprocess, SDK) under `tests/harness/`. Production's import graph never contains
   `tests`; harness modules do not import the test framework.
3. **Write the spine test.** Real entry, real collaborators, per-test temp dir, boundary
   substitutes only. Heavy is fine. Name it after the capability.
4. **Fill the branch matrix.** Success / invalid input / downstream failure / empty /
   repeat — one test per cell.
5. **Cover important behaviors.** Pick by change frequency and reuse across entries. Do
   not chase repo-wide percentage.
6. **Self-check.** Behavior-preserving refactor → all green. Red → delete/rewrite the
   test, never touch production. A necessary production edit → `C`.

---

## C. Architecture Blocker

Trigger: a core behavior cannot be observed without editing production, even through the
real entry with boundary substitutes.

Forbidden: mocking the coupling away and calling it covered; temporary seams; test-only
branches; silently lowering the coverage target.

```
## Architecture Blocker
Behavior:   <what must be protected>
Blocked by: <coupling — file:line, why unobservable>
Rejected:   <workaround considered, and what it would hide>
Minimal seam: <smallest change that unblocks a contract test>
Handoff:    /brooks-debt on <module>, then return here
```

---

## Deletion Ledger

`tests/DELETION_LEDGER.md`, append-only. Protection is not lost, only deferred to a
better instrument.

```markdown
| date | deleted test | behavior it protected | why deleted | rebuild as | priority |
|------|--------------|----------------------|-------------|------------|----------|
| 2026-10-26 | test_internal_cache_order | cache eviction order | G2: asserted private dict order | spine test via `svc.run()` + temp dir | core |
```

`why deleted` names G1/G2/G3. `rebuild as` names the boundary and entry, not "later".
`priority`: core / important. Re-read before finishing: any `core` row still without a
replacement is 🔴 G3.
