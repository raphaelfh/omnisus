# AGENTS.md

omnisus brings Brazilian public health data (DATASUS, IBGE, CNES) into a local
DuckLake lake, with the provenance a researcher needs to cite each result. This file
is the contract for every change, by a person or an agent. `CONTRIBUTING.md` says the
same to contributors in Portuguese; when they disagree, this file wins.

Read it in order: the pillars say what omnisus promises, the policy says how a change
keeps those promises, and the rest says how to work here.

## Pillars

What a researcher can rely on. A change that breaks one of these is a bug, however
small the diff.

1. **Citable.** Every imported row traces back to the server file it came from: a
   *publication* records the scope, the server path and the SHA-256, and `odb.cite`
   turns a snapshot into a citation. An importer that writes a scope without its
   publication breaks this promise.
2. **Never guessed.** Codes stay as DATASUS published them. A label comes only from
   the dictionary; a code the dictionary does not know has no label. Each code map
   carries a claim with its status (`verified_in_source`, `conflicting`,
   `unreviewed`) and evidence. Harmonised categories exist only for validated
   sources (ADR 0003).
3. **Verifiable.** Whoever doubts a fact can check it: the documents behind the
   dictionaries are registered with URL and SHA-256, audits live in `evidence/`, and
   `odb.check_columns` shows empty values, unknown codes and date ranges.
4. **Simple.** One mechanism for each job, no dead code, code and docs a newcomer
   reads once. A curated dataset and a user-built `Dataset` take the same path
   (ADR 0002).
5. **Public.** The repository, its history and its fixtures are public; nothing about
   a person or a contributor's machine enters them.

## Zero-assumption policy

These rules apply to every change in this repository. Code and tests cite them by
number ("AGENTS.md rule 2"); keep the numbering.

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

When a rule and a deadline conflict, the rule wins: leave the gap open in an issue
rather than fill it with a guess.

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

## Where things live

| What | Where |
| --- | --- |
| Glossary: use its terms in code, tests and issues | `CONTEXT.md` |
| Decisions (ADRs); say so when a change contradicts one | `docs/decisions/` |
| Dataset registry | `src/omnisus/sources/datasus_ftp/datasets.py` |
| Dictionaries: fields, codes, labels, claims | `src/omnisus/data/dicionarios/<dataset>.yaml` |
| Official documents cited by the dictionaries | `src/omnisus/data/dicionarios/sources/registry.json` |
| Test fixtures and their provenance | `tests/fixtures/`, `tests/fixtures/FIXTURES.md` |
| Audits that code, dictionaries, tests or docs cite | `evidence/` |
| Dictionary maintenance, step by step | `docs/dicionario/manutencao.md` |

Generated files are regenerated, never edited by hand: `docs/datasets.md`
(`scripts/gen_datasets_doc.py`), the CNV code maps and the SINAN and SIM subset
dictionaries (`scripts/metadados/`). Researcher pages (`docs/pesquisa/`,
`docs/sources/`, `docs/dicionario/`) are in Portuguese; technical guides and the API
reference are in English.

## Commands

```bash
uv sync --locked --all-extras        # set up
uv run ruff check .                  # the same checks as CI, in CI order
uv run ruff format --check .
uv run mypy src
uv run marimo check --strict --ignore-scripts notebooks
uv run python scripts/gen_datasets_doc.py --check
uv run pytest -m "not e2e and not perf" -n auto
uv run mkdocs build --strict
```

Tests marked `integration` and `e2e` reach the DATASUS server and stay out of pull
request CI; run them when a change depends on what the server lists today.

## Definition of done

A change is ready for review when:

- the red run of its new test is recorded in the pull request (rule 3);
- every new fixture has a row in `FIXTURES.md` and every new fact cites the server or
  a hashed artifact (rules 1 and 2);
- the pull request lists what it deleted, or says it deleted nothing (rule 4);
- the checks under [Commands](#commands) pass, and generated files are current;
- a contradicted ADR is named, and `CONTEXT.md` is updated when a term changes;
- `git diff --cached` shows nothing from the public-repository list above.

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
