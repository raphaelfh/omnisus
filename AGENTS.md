# AGENTS.md

## This repository is public

Everything committed here is published: code, docs, fixtures, evidence, commit
messages and pull request text. Git history keeps a file after it is deleted, so
check `git diff --cached` before every commit. Never commit:

- credentials, tokens, or connection strings with a password (tests use obvious
  placeholders such as `user:dummy`);
- absolute local paths (`/Users/...`, `/home/...`), machine names, or anything else
  that describes a contributor's computer;
- names, modules, plans or tasks of private projects, clients or other repositories;
- personal data. Fixtures are excerpts of public DATASUS files without person
  identifiers; a dataset that names people (CPF, CNS, name), such as CNES `PF`, is
  out of scope;
- agent working files: plans, specs, progress notes, handoffs, review transcripts,
  test or lint logs. Plans and decisions live in GitHub Issues and pull requests;
  a skill that writes a plan or spec to a file writes it to an issue instead.

Evidence enters `evidence/` only when code, a dictionary, a test or a doc cites it,
and it records the SHA-256 of what it read. If something private reaches a pushed
commit, deleting it in a new commit does not remove it: stop and tell the maintainer.

## Zero-assumption policy

These rules apply to every change in this repository.

1. **Facts come from the server or from a hashed artifact.** A directory,
   filename shape, code list, layout or label enters code or docs only after it
   was read from the live DATASUS server or from an archived file whose SHA-256
   is recorded. "Not published" needs the same evidence as "published".
2. **Tests run on real data.** Semantics are tested against committed excerpts
   of real DATASUS files, each listed with its provenance in
   `tests/fixtures/FIXTURES.md`. Synthetic bytes are allowed only for
   malformed-input cases of the decoder, and the test says so.
3. **TDD, red first.** Every behaviour change starts with a failing test on
   real data. The pull request records the red run. A test that cannot be made
   to fail proves nothing.
4. **No dead code.** Every function, column, script or fixture lands with a
   consumer or a test in the same change, and is deleted with its last
   consumer. Pull requests list their deletions.
5. **Keep it simple and readable.** Prefer one mechanism over two, a plain
   function over a framework, a generated file over a loader feature. Write
   code and docs to be read once by someone who did not write them. If a rule
   needs a diagram to be understood, simplify the rule.

## Domain

`CONTEXT.md` is the glossary; use its terms in code, tests and issues.
`docs/decisions/` holds the ADRs; say so when a change contradicts one.

## Agent workflow

Issues live in GitHub Issues; use the `gh` CLI. See `docs/agents/issue-tracker.md`.
Triage labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`,
`wontfix` (`docs/agents/triage-labels.md`).

<!-- curated-engineering:start -->
### Engineering skill routing

Use the personal curated engineering selection documented in `docs/agents/skill-routing.md`.
Superpowers (`sp-*`) owns the development workflow. Matt Pocock (`mp-*`) provides
specialized domain/interface guidance and narrowly scoped utilities.

- Select one owner per stage; state the owner briefly when overlap is possible.
- Reuse decisions, approvals, plans, test results and reviews that remain valid.
- Use `sp-executing-plans` for inline execution by default. Use
  `sp-subagent-driven-development` only when delegated execution is selected and permitted.
  Tool availability alone does not change execution mode.
- Use `sp-test-driven-development` as the only TDD procedure (red-green-refactor)
  and `sp-systematic-debugging` as the only diagnosis procedure.
- `mp-domain-modeling` and `mp-codebase-design` return findings to the active workflow;
  they do not begin another interview or plan.
- `mp-research` handles external research, not routine repository reading.
- `mp-grilling` and `mp-wizard` require explicit invocation. A grilling interview replaces
  other interviews for the same decisions.
- Review-only, research-only and plan-only requests end with their requested deliverables.
- Follow explicit user choices over defaults. Do not activate a second equivalent workflow
  to satisfy the same stage. If a chosen skill is unavailable, report it instead of loading
  a disabled plugin from its cache.
<!-- curated-engineering:end -->
