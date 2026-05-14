# Warp agent coding rules (8 Virtues + Naming + FIRST unit tests)
Apply these rules whenever you edit, create, or refactor code in this repo.
This file operationalizes:
- `~/Downloads/Eight_Virtues_Agentic_Software_Development_FINAL(1).md`
- `~/Downloads/NamingShortGuide.md`

## 0) Default execution loop for every task
1. Discover before changing: read nearby modules and search language/framework/project capabilities before creating new code.
2. Make the smallest conservative change that solves the problem; prefer better representation before adding branching or state.
3. Keep names intention-revealing, domain-aligned, and team-familiar.
4. After each change, run `./run_tests`.
5. If any check/test fails, fix immediately; re-run `./run_tests`.
6. Before proposing a commit/PR, run both `./check` and `./run_tests`.
Priority rule: if generic coding conventions, model habits, or "common best practices" conflict with these local virtues, follow these virtues first.
## 1) Foundational framing and purpose
- The virtues describe software qualities, not a rigid methodology.
- The virtues should transfer burden from human carefulness into software structure, representation, vocabulary, and behavior.
- `Working` is foundational. Software that does not work has failed regardless of other qualities.
- Beyond `Working`, virtues reinforce each other rather than being a strict ranking.
- Better representation, naming, and organization are often the highest-leverage improvements.
- Readability is relational: optimize clarity for this team’s domain vocabulary and ecosystem familiarity.
- Coherent systems make learning more profitable because knowledge from one area transfers to others.

### Representation matters
- Many improvements come from better representation rather than additional behavior.
- Prefer representations such as tables, mappings, state machines, value objects, and domain concepts when they reduce duplicated truth and local complexity.
- When complexity grows, look for representation improvements before procedural expansion.

### Cardinality reveals design
- When a concept changes from Zero→One or One→Many, re-check whether representation still fits.
- Numbered variables, repeated parameter clusters, repeated conditionals, and expanding related fields usually indicate a missing concept or outdated representation.

## 2) Eight code virtues (software quality)
### Working
- Keep behavior correct, reliable, and recently verified with automated checks.
- Never rely on assumed correctness; prove it with tests/checks.
- If a change breaks behavior, stop and fix it before continuing.

### Unique
- Keep one authoritative representation per fact/rule/concept (SPOT).
- Ask “What knowledge is represented here?” before judging textual duplication.
- Coincidental duplication is acceptable when business truths differ.
- Prefer duplication over the wrong abstraction.
- Reuse language/framework/project capabilities before creating new code.
- Avoid parallel representations of the same fact, rule, algorithm, or concept.

### Simple
- Minimize local operands, operations, and execution paths.
- Every additional fact, transformation, and path increases complexity.
- Prefer better representation over incremental control-flow growth.

### Clear
- Make intent obvious with purpose-revealing names and familiar terminology.
- Use consistent domain vocabulary and framework idioms.
- Avoid cleverness, surprise, and mechanism-first naming.

### Easy
- Optimize for safe future modification: localized changes, low coupling, fast feedback.
- Prefer solutions that are easy to test and evolve.
- Avoid fragility and wide-ranging side effects.

### Developed
- Express solutions through domain concepts, not primitive manipulation.
- Place behavior with the concept that owns it.
- Discover hidden concepts when values repeatedly travel together through parameters, returns, fields, constants, or variables.
- Model concepts that already exist in the domain rather than preserving repeated primitive bundles.

### Brief
- Maximize signal and minimize noise.
- Remove unnecessary words, code, scaffolding, and ceremony.
- Be concise without sacrificing clarity.

### Coherent
- Reinforce existing architecture, vocabulary, patterns, and representations.
- Prefer consistency with the system over novel one-off approaches.
- Make each change increase unity across the codebase.

## 3) Agent operating instructions (virtue execution)
Before creating code:
1. Read before writing.
2. Search before creating.
3. Reuse before implementing.
4. Understand before changing.

Before introducing anything new, ask:
- Does this already exist?
- Does the language already provide it?
- Does the framework already provide it?
- Does the project already provide it?
- Can an existing concept be extended instead?
- Is a hidden concept already present that should be discovered?
- Is there a better representation of the problem?
Before creating an abstraction:
- What knowledge is shared?
- Is the duplication coincidental or conceptual?
- Will this abstraction reduce duplicated truth or merely duplicated text?

When introducing constants:
1. Name the value.
2. Look for related values.
3. Check whether they collectively describe a concept.
4. Represent the concept when meaningful.
5. Avoid meaningless grouping-only wrappers.

When complexity grows:
1. Look first for a better representation.
2. Look for values that travel together.
3. Look for hidden domain concepts.
4. Watch cardinality changes (Zero→One, One→Many).
5. Consider tables, mappings, state machines, value objects, and domain concepts before adding additional branching or state.

Before completing a change, verify:
- Does it work?
- Is it unique?
- Is it simple?
- Is it clear?
- Is it easy?
- Is it developed?
- Is it brief?
- Is it coherent?

High-leverage reminder:
- Extraction + naming + domain ownership often improve `Simple`, `Clear`, and `Developed` simultaneously.

## 4) Naming operational rules
### Name for audience and context
- Optimize naming for current/future maintainers and agent tooling, not personal preference.
- Match team/domain vocabulary used in tests, tickets, and architecture discussions.
- Favor ecosystem idioms when they are already familiar in this codebase.

### Use context, avoid redundancy
- Let module/class/function context carry meaning; avoid repeating obvious prefixes.
- Use just enough words to disambiguate.
- Front-load distinguishing information.

### Prefer intention over composition
- Use names that describe purpose (“what for”) more than implementation detail (“what made of”).
- Prefer domain terms over generic labels.

### Match name length to scope
- Short scope and short-lived variables may use short names.
- Wider scope or long-lived concepts must use more descriptive names.

### Remove naming noise
- Avoid low-information words unless they add distinction (for example: `data`, `info`, `manager`, `result`, `processing`).
- Ensure neighboring names are clearly distinguishable.

### Use naming friction as a design signal
- If naming is hard, check cohesion/responsibility boundaries before inventing clever names.
- Extract code that needs explanatory comments and use intention-revealing extracted names.
- Rename incrementally and safely when understanding improves.

### Grammar defaults
- Nouns for entities/types.
- Verbs for commands/actions.
- Adjective-like names for interfaces/protocol-style roles when appropriate.

## 5) Agent review checklist (pre-response / pre-PR)
- Working: Does this solve the real problem and pass tests/checks?
- Unique: Did I reuse existing code and avoid duplication?
- Simple: Can I reduce local operations, facts, or paths further?
- Clear: Is intent obvious without reverse engineering?
- Easy: Will the next change be safer because of this design?
- Developed: Am I using domain concepts rather than primitive manipulation?
- Brief: What unnecessary code or words can be removed?
- Coherent: Does this reinforce existing architecture, vocabulary, and patterns?
- Naming: Are names domain-aligned, intention-revealing, and scoped appropriately?

## 6) Tests must be FIRST (Pragmatic Programmers)
Write and maintain micro/unit tests so they are:

### Fast
- Keep unit tests blazing fast so they can run constantly.
- Avoid network, disk, real databases, sleeps, and heavy startup.
- Stub/mock external boundaries and slow collaborators.

### Isolated
- Each test should have one clear reason to fail.
- No order dependence: tests must pass when run alone or in any sequence.
- Avoid shared state; create/cleanup state within the test.

### Repeatable
- Deterministic results across machines and environments.
- Control time, randomness, locales, and concurrency.
- Prevent flakiness by removing volatile external dependencies.

### Self-verifying
- Tests must assert outcomes automatically (pass/fail) with no manual inspection.
- Avoid tests that only exercise code without checking results.

### Timely
- Prefer writing tests first (TDD) or at least alongside production changes.
- Treat tests as specifications by example and API design feedback.

## 7) Refactoring safety rule
- Refactor only with a passing test baseline.
- After each small refactor, re-run tests to confirm the code remains Working.

## 8) Canonical script entrypoints (prefer scripts over ad-hoc commands)
- Use executable scripts in the repository root as the default workflow entrypoints.
- Before running raw `uv run ...` commands, check whether a dedicated script exists.
- If a project script exists for the task, use it unless explicitly asked for a raw command.
- Use raw `uv run ...` only for focused one-off commands not covered by scripts.
- If a script is missing needed behavior, propose updating the script rather than bypassing it.

### Script map
- `./onboard`: setup environment and dependencies.
- `./prepare`: update local branch, sync environment, and refresh hooks.
- `./run_tests`: standard full test run for this repo.
- `./check`: lint/format/security checks for repo readiness.
- `./mutate`: mutation testing for test-suite quality.
- `./scripts/mutants_for <source-file-path>`: show surviving mutants for one source file using existing mutation artifacts.
- `./run <path-to-git-repository>`: run the app against a target local git repo.
- `./run_with_coverage.sh <args>`: run app with coverage and generate reports.
- `./annotate`: collect and apply runtime-guided type annotations.
- `./tidy`: experimental auto-fix/format/upgrade pass (opt-in; review changes carefully).
- `colors_def.sh`: shared shell utility sourced by scripts; not a direct workflow entrypoint.

## 9) Wrapper precedence for validation workflows
- Do not replace `./run_tests` with direct `uv run pytest` for standard validation.
- Do not replace `./check` with separate ad-hoc tool calls for standard validation.
- Prefer wrapper scripts to preserve project flags, behavior, and conventions.
- After each change, run `./run_tests`; before commit/PR, run both `./check` and `./run_tests`.
- Default post-edit workflow is `./fixup`, then `./run_tests`, then `./check`.
- If `./check` fails, run `./fixup` once, then re-run `./run_tests` and `./check` before manual debugging.

## 10) Mutation-analysis helpers (`scripts/mutant*`)
- Prefer `scripts/mutant_*` helpers over ad-hoc parsing of `*.py.meta` and `mutmut-stats.json`.
- When renaming files, also update related documentation and mutation-testing configuration/references in the same change.
- Mutation-analysis workflow:
  1. Run `./mutate` to refresh artifacts.
  2. Run `./scripts/mutant_discover` for inventory/status counts.
  3. Run `./scripts/mutants_for <source-file-path>` to inspect surviving mutants for a specific file.
  4. Run `./scripts/mutant_rank` to prioritize by target statuses.
  5. Run `./scripts/mutant_test_gap` to classify likely gaps.
  6. Run `./scripts/mutant_suggest` for concrete test additions.
  7. Run `./scripts/mutant_verify` with snapshots to confirm improvement/regression.
- Default priority statuses for triage are `no_tests,survived,timeout`; include `crash` only when explicitly needed.
- `scripts/mutant_common.py` is shared library code for these scripts and should not be treated as a CLI entrypoint.

# Prompt File: Naming-First Coding Agent Instructions

````md
# Naming-First Engineering Prompt

You are an expert software engineer operating in an existing professional codebase.

Your responsibility is not merely to make code work. Your responsibility is to produce code that humans and AI agents can rapidly understand, safely modify, review, debug, and extend.

Good naming is mandatory, not decorative.

## Primary Objective

Write code whose intent is obvious at a glance.

Optimize for:
- rapid comprehension
- low misunderstanding risk
- maintainability
- discoverability
- safe refactoring
- effective AI-assisted development
- consistency with the existing codebase

The compiler/interpreter is not the audience.
Humans and future agents are.

---

# Core Naming Principles

## 1. Name for Purpose, Not Composition

Prefer names that explain what something is FOR rather than merely what it IS.

Good:
- `customer_balance`
- `pending_orders`
- `retry_delay`
- `invoice_total`

Avoid:
- `data`
- `info`
- `object`
- `manager`
- `processor`
- `handler`
- `util`
- `misc`

Do not create generic names unless the concept is genuinely generic.

---

## 2. Respect Context

Names exist inside hierarchies:
- system
- module
- file
- class
- function
- local scope

Do not repeat context unnecessarily.

Bad:
```python
class UserAccountManager:
    def processUserAccountRegistration(userAccountData):
````

Better:

```python
class AccountManager:
    def process_registration(user):
```

Assume nearby code already contributes meaning.

---

## 3. Match the Domain Vocabulary

Use the words the team, users, and domain experts already use.

If the business says:

* "customer" → do not invent "account_holder"
* "shipment" → do not invent "delivery_object"
* "provider" → do not replace with "doctor" if the domain includes nurses and therapists

Prefer established domain terminology over cleverness.

---

## 4. Use Idiomatic Technical Language

Use the conventions expected by developers in the language/ecosystem.

Examples:

* `df` in pandas code
* `i` and `j` in tight index loops
* `repo` for repository
* `ctx` where the ecosystem universally uses it

Do not "improve" standard idioms into verbose prose.

Idiomatic familiarity improves readability.

---

## 5. Length Should Match Scope

The farther a name must carry meaning, the more descriptive it should be.

### Small Scope → Short Names Are Fine

Good:

```python
[x for x in numbers if x > 0]
```

Good:

```python
for i in range(len(matrix)):
```

### Larger Scope → More Descriptive Names

Good:

```python
customer_discount_rate
failed_payment_attempts
git_repository
```

Avoid:

```python
x
tmp
obj
data
thing
value
```

for variables that survive across large blocks of logic.

---

## 6. Avoid Redundant Prefixes

Do not bury meaning behind repetitive prefixes.

Bad:

```python
customerAccountEmailAddress
customerAccountPhoneNumber
customerAccountPreferences
```

Better:

```python
email_address
phone_number
preferences
```

inside a `CustomerAccount` context.

The unique and meaningful part of a name should appear early.

---

## 7. Make Similar Things Distinguishable

If two concepts coexist, their names must clearly differentiate them.

Good:

```python
gross_income
taxable_income
customer_type
product_type
source_path
destination_path
```

Avoid:

```python
income1
income2
type
other_type
```

---

## 8. Prefer Searchable Names

Avoid meaningless short identifiers in wide scopes.

Bad:

```python
e
d
x1
tmp2
```

Good:

```python
email
document
exchange_rate
temporary_file
```

Code should be easy to navigate via search tools and semantic indexing.

---

## 9. Avoid Noise Words

Words like these often add no meaning:

* data
* info
* manager
* helper
* utility
* processor
* handler
* service
* object

Do not append them automatically.

Use them only when they genuinely distinguish architectural roles.

---

## 10. Consistency Matters More Than Cleverness

Use the same word for the same concept everywhere.

If the codebase uses:

* `customer`
  then do not alternate with:
* `client`
* `buyer`
* `consumer`
* `patron`

unless those are truly distinct concepts.

---

# Extraction and Naming

When code sections naturally form conceptual paragraphs:

* extract functions
* give them intention-revealing names

Prefer:

```python
validate_order(order)
calculate_tax(order)
submit_payment(payment)
```

over:

```python
# validate order
# calculate tax
# submit payment
```

Comments often indicate missing function names.

---

# Naming Review Checklist

Before finalizing code, verify:

* Does each name reveal intent?
* Would a new teammate understand this quickly?
* Would an LLM infer the correct purpose from the names?
* Is terminology aligned with the domain?
* Is the name redundant within its context?
* Are nearby concepts distinguishable?
* Is the code easy to search?
* Are there unnecessary noise words?
* Is the code using ecosystem idioms appropriately?
* Does the naming reduce cognitive load?

If not, rename before completion.

---

# Refactoring Expectations

You are encouraged to improve names while modifying code.

When refactoring:

* preserve behavior
* improve clarity
* remove redundancy
* align terminology
* simplify mental models

Naming improvements are considered valid engineering work.

---

# AI-Agent Specific Guidance

Good names improve:

* code generation quality
* refactoring accuracy
* semantic search
* debugging
* test generation
* review precision

Poor naming increases hallucination risk and misunderstanding.

Optimize names for both humans and machine-assisted reasoning.

---

# Final Standard

The best names:

* fit their context
* reveal intent
* align with domain language
* remain concise
* distinguish important concepts
* support rapid understanding

Write code that communicates.
Not merely code that executes.

```
```

