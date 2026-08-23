# Architecture quality guide

Use this guide to decide whether the report is merely descriptive or strong enough for architecture approval.

## Translate concepts before symbols

Explain the business responsibility first, then attach code evidence.

| Architecture term | Plain-language translation | Evidence to show |
| --- | --- | --- |
| Module | The place that owns one kind of decision | Public entry points and files behind them |
| Interface | What callers must know | Inputs, outputs, errors, and guarantees |
| Implementation | Details callers should not need to know | Helpers or libraries hidden behind the interface |
| Boundary / seam | The hand-off point between responsibilities | Direction of calls and converted data |
| Adapter | A translator for one external format or system | External type in, internal type out |
| Invariant | A rule that must always remain true | Validation location and failure behavior |
| Dependency direction | Who is allowed to know whom | Allowed and forbidden arrows |
| Migration | How to reach the new design without a risky jump | Ordered, reversible stages and rollback |

Do not use an analogy unless it clarifies a real responsibility. State where the analogy stops matching the code.

## Judge a proposed module

A useful module hides substantial decisions behind a smaller interface. Check:

1. **Depth**: callers learn fewer concepts than the module contains.
2. **Leverage**: one interface supports more than one real workflow or caller without flags for unrelated cases.
3. **Information hiding**: vendor formats, transport details, state bookkeeping, or policy choices stay behind the boundary.
4. **Locality**: one product change usually touches one obvious place.
5. **Testability**: observable guarantees can be tested without asserting private helper choreography.
6. **Navigability**: a new engineer can find the owner from domain language and public entry points.

Apply two quick stress tests:

- **Deletion test**: if the proposed module vanished, would callers need to relearn meaningful policy or merely copy a tiny helper?
- **Second-use test**: identify two real uses before generalizing. A hypothetical future use is not enough evidence.

Call out a shallow wrapper, flag-heavy API, leaking vendor type, circular dependency, or pass-through abstraction as a risk rather than praising it as architecture.

## Define the interface contract

For each public operation, capture only applicable fields:

| Field | Question |
| --- | --- |
| Responsibility | What decision or work does this operation own? |
| Caller | Which layer or actor may call it? |
| Input | Which domain data is required? Who validates it? |
| Output | What stable domain result is returned? |
| Invariants | What must be true before and after the call? |
| Errors | Which failures are distinguishable, retryable, user-visible, or logged? |
| Side effects | What network, storage, cache, clock, or UI state can change? |
| Idempotency | What happens if the operation is repeated? |
| Concurrency | What happens under duplicate or overlapping work? |
| Visibility | Which items are public, crate/package-visible, or private? |
| Performance | Which latency, size, or call-count constraint matters? |

Prefer one cohesive operation over exposing construction, validation, conversion, and dispatch as separate public steps when callers do not need that control.

## Show dependency and runtime direction

Use two views when both matter:

- **Static dependency**: compile/import knowledge such as `UI -> application -> domain <- adapter`.
- **Runtime sequence**: what happens during a request, event, hydration, job, or retry.

Name forbidden arrows, not only desired arrows. If server and client builds differ, show both compile targets and shared-code restrictions. If an external service is involved, show the internal domain type and the adapter conversion point.

## State behavior and change impact

Classify product effects:

- **Direct**: the user-visible workflow intentionally changes.
- **Indirect**: shared state, caching, navigation, authorization, scheduling, or error handling may change.
- **Unaffected**: inspected behavior intentionally remains the same.
- **Unknown**: not verified; never silently place it under unaffected.

Tie every changed file or module to a responsibility and behavior. Avoid exhaustive symbol inventories.

## Make migration credible

Each migration stage must have:

- one observable outcome;
- compatibility with the previous stage when required;
- focused tests;
- a rollback action;
- a clear condition for deleting temporary code.

Prefer adding a new contract, moving one caller at a time, verifying behavior, and deleting the old path last. State whether data migration, API compatibility, feature flags, or dual writes are unnecessary as well as when they are required.

## Define verification and acceptance

Test the public contract and product outcome. Include, as applicable:

- happy path and boundary values;
- invalid input and external failures;
- retry, idempotency, or concurrent work;
- server/client or multi-target compilation;
- authorization and data exposure;
- observability signals;
- rollback or compatibility behavior;
- an end-to-end smoke path that avoids unsafe production writes.

Write acceptance criteria as observable statements. Avoid criteria such as “code is clean,” “architecture is improved,” or “all tests pass” without naming the important behavior.

## Record decisions at the right weight

Keep a decision in the report when it is local and easy to reverse. Recommend an ADR when it:

- changes a cross-module dependency rule;
- establishes shared domain language or ownership;
- selects a costly or difficult-to-reverse technology;
- has a surprising constraint future maintainers may otherwise remove;
- rejects a plausible alternative for a durable reason.

For each decision, record date, status, choice, rationale, tradeoff, and affected sections.

## Approval readiness checklist

An architect should be able to answer yes to all applicable questions:

- Is the current state supported by code evidence?
- Are facts and proposals visually distinct?
- Is ownership explicit?
- Is the public contract smaller than the hidden implementation?
- Are allowed and forbidden dependencies clear?
- Are invariants and failure behavior explicit?
- Are product effects and unaffected behavior named?
- Can the migration be performed and rolled back in small stages?
- Do tests verify public behavior rather than private choreography?
- Are non-goals, alternatives, and top risks visible?
- Are all approval-blocking decisions resolved?
- Is the end state, including temporary-code deletion, defined?
