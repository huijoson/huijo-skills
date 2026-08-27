---
name: architecture-spec
description: >-
  Create a two-layer architecture specification as a visual HTML report: a
  plain-language main section for product and engineering readers plus an
  architect appendix covering contracts, dependency direction, invariants,
  failure policy, migration, tests, and acceptance criteria. Use when a user
  asks for an architecture spec, architecture review, module-deepening
  proposal, Before/After architecture diagrams, 架構規格, 雙層架構規格,
  程式碼架構, or 架構師附錄. Also use when change scope (改動範圍) or
  functional impact (功能影響) is requested as part of an architecture diagram,
  architect appendix, or two-layer HTML artifact. Inspect the codebase first and resolve design
  choices one question at a time. Do not use for implementation-only
  requests, a narrow code review with no design artifact, or a simple impact
  summary that does not request architectural analysis.
license: MIT
---

# Architecture Spec

Create one living architecture document that non-architects can understand and architects can approve. Separate repository facts from proposals, and keep implementation outside this workflow until the user explicitly requests it.

## Required resources

Before drafting, read `references/architecture-quality.md` completely. Use `assets/report-template.html` as the visual and structural starting point; copy it to a new output file rather than editing the asset.

## Workflow

### 1. Establish the request and evidence

Treat the text after the skill invocation as the topic and requested outcome. The invocation may arrive as `$architecture-spec`, `/architecture-spec`, `architecture-spec`, or a plain request that matches this skill's description — treat all forms identically. If no topic is supplied, infer it from the current conversation; ask only when the scope cannot be determined safely.

Inspect before asking questions:

1. Read the applicable agent instructions, repository status, domain glossary, ADRs, and project documentation.
2. Trace the relevant entry points, state/data flow, tests, persistence or external API boundaries, and user-visible behavior.
3. Search by domain concept and behavior before following individual variables.
4. Record exact `path:line` evidence for important current-state claims.
5. Preserve unrelated working-tree changes and never treat uncommitted code as disposable.

When documenting an existing change, establish and label the comparison point before mapping scope: working tree versus `HEAD`, branch versus merge base, or a user-supplied revision. If it cannot be inferred and materially changes the conclusions, ask one scope question.

Do not ask the user for facts discoverable from the repository. Label every material statement as one of:

- **Observed**: directly supported by current code or documentation.
- **Proposed**: a design recommendation not yet accepted.
- **Decided**: explicitly accepted by the user or an authoritative record.
- **Open**: a decision still needed.

Completion criterion: the current behavior, desired outcome, affected boundary, and unknown design decisions are distinct.

### 2. Build the scope and impact model

Map the change in domain language before naming variables or helper functions. Capture:

- the problem and why it matters;
- the current end-to-end flow;
- the proposed responsibility boundary;
- files or modules to add, modify, read only, and intentionally leave untouched;
- directly affected, indirectly affected, and unaffected product behavior;
- architecture techniques being proposed, their plain-language meaning, why each fits, and its tradeoff;
- the highest-risk assumption and the smallest useful rollback boundary.

Prefer a few stable business concepts over a graph of every symbol. Show technical names only as traceable evidence under the plain-language explanation.

Completion criterion: a reader can say what changes, what does not, and which user behavior could move.

### 3. Draft the two-layer HTML

Copy `assets/report-template.html` to a fresh, timestamped file in the platform's temporary directory unless the user requests a repository path. Replace every `{{PLACEHOLDER}}`, localize visible labels to the user's language, and remove unused rows or sections. HTML-escape user-supplied and repository-sourced text before inserting it into HTML or Mermaid labels. Keep the report self-contained except for the optional Mermaid CDN used for diagrams.

The first layer must be understandable without reading source code:

1. one-sentence outcome and a short problem explanation;
2. simple Before and After flow diagrams;
3. change-scope map with add / modify / read-only / untouched status;
4. functional-impact table including explicitly unaffected behavior;
5. architecture techniques translated into plain language;
6. top risk, current recommendation, and open decision.

The architect appendix must make approval possible:

1. context, boundary, non-goals, and ownership;
2. interface contract: caller, inputs, outputs, invariants, errors, side effects, visibility, and relevant performance constraints;
3. allowed and forbidden dependency directions plus runtime/data sequence;
4. failure, security, privacy, authorization, observability, and concurrency policy as applicable;
5. staged migration with compatibility, rollback, and deletion/end-state criteria;
6. contract-level tests, acceptance criteria, and evidence required before completion;
7. alternatives, risks, decision log, and ADR recommendation.

Use diagrams only for relationships that prose cannot show as clearly. Keep each diagram to a small number of domain-level nodes. Make every code reference secondary to the behavior it supports. Treat Mermaid as an enhancement: when external CDN access is unavailable, use inline SVG or simple HTML/CSS flow diagrams for the required Before/After views.

To prevent Mermaid rendering errors:
- Always quote node labels containing special characters, brackets, or parentheses: e.g. `node["Label (Details)"]`.
- Never use unescaped angle brackets or raw stereotypes like `<<interface>>` in flowchart labels; use `«interface»`, `&laquo;interface&raquo;`, or `[interface]`.
- For multi-line labels inside flowchart nodes, use `<br/>` instead of `\n`.
- Avoid embedding raw unescaped HTML tags in labels.

Completion criterion: the HTML opens on its own, contains no unresolved template tokens, and clearly separates Observed, Proposed, Decided, and Open content.

### 4. Resolve decisions one question at a time

If approval-blocking Open items exist after presenting the initial report, ask exactly one decision question per turn. For each question:

- explain the decision in plain language;
- offer two or three materially different choices;
- recommend one choice and explain the concrete tradeoff;
- state which report sections and product behaviors the answer changes.

Ask the highest-leverage question first. Do not bundle decisions or repeat questions already answered. After each answer, update the same HTML file, move the item from Open to Decided, and then ask the next question.

If no approval-blocking Open item exists, do not invent a question; ask the user to confirm the documented design and proceed to handoff. Otherwise continue until the user confirms the design or asks to stop. Do not modify product code, create implementation commits, or publish an ADR during this workflow unless the user separately authorizes that action. Recommend an ADR when a decision is hard to reverse, surprising, or establishes a cross-module rule.

Completion criterion: no approval-blocking Open item remains and the user's decisions are reflected in the artifact.

### 5. Hand off the result

Return:

- a clickable path to the final HTML;
- a short summary of the chosen architecture and product impact;
- remaining risks or explicitly deferred decisions;
- whether an ADR is warranted;
- the next safe step, usually an implementation plan rather than immediate implementation.

If evidence is incomplete, say exactly what was not verified. Never present a proposal as current code behavior.

## Invocation examples

The prefix depends on the host agent:

- **Codex**: `$architecture-spec <topic>`
- **Claude Code & Copilot CLI**: `/architecture-spec <topic>`
- **Antigravity & Kiro CLI**: `architecture-spec <topic>` or natural language prompt (in Antigravity, leading `/` is reserved for client-side UI shortcuts, so custom skills are triggered by name or semantic description matching)
- **Plain language**: A request that matches the description above is always a valid invocation across all agents.

```text
$architecture-spec Deepen the Schedule Event module
```

```text
/architecture-spec 請把付款流程重構畫成雙層架構規格 HTML，先查程式碼，一次問我一個決策。
```

```text
architecture-spec 請針對 inline-agent 產出雙層架構規格報告
```

```text
請產生這次權限模組改動的白話架構圖與架構師附錄，列出功能影響、migration 與 acceptance criteria。
```
