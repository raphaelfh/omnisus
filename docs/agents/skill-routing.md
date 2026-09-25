# Engineering skill routing

The maintainer's curated selection of Superpowers (`sp-*`) and Matt Pocock (`mp-*`)
skills. It is a personal configuration, not a dependency: contributors without these
skills follow `AGENTS.md` and the zero-assumption policy directly.

## Owners

| Stage | Owner |
| --- | --- |
| Unsettled software design | `sp-brainstorming` |
| Agreed multi-step design requiring a plan | `sp-writing-plans` |
| Approved bounded change | Direct implementation using the TDD discipline |
| Inline execution (default) | `sp-executing-plans` |
| Selected delegated execution | `sp-subagent-driven-development` |
| Diagnosis | `sp-systematic-debugging` |
| TDD | `sp-test-driven-development` |
| Concrete code review | `sp-requesting-code-review` |
| Existing review feedback | `sp-receiving-code-review` |
| Completion evidence | `sp-verification-before-completion` |
| Git isolation and finishing | `sp-using-git-worktrees`, `sp-finishing-a-development-branch` |
| Requested parallel investigation outside a plan | `sp-dispatching-parallel-agents` |
| Business concepts | `mp-domain-modeling` |
| Interface design reference | `mp-codebase-design` |
| External primary-source research | `mp-research` |
| Actual merge/rebase conflicts | `mp-resolving-merge-conflicts` |
| Explicit decision interview | `mp-grilling` |
| Explicit manual terminal wizard | `mp-wizard` |

`sp-using-superpowers` routes coding work and does not own an additional execution
stage. Domain and interface specialists return to the caller. A standalone review,
research request, or plan request ends with its own deliverable. Existing project
conventions for issues/specs and domain documentation still apply.
