# Warp agent coding rules (7 Code Virtues + FIRST unit tests)
Apply these rules whenever you edit, create, or refactor code in this repo.

## 1) Prefer virtuous code (Industrial Logic: 7 Code Virtues)
Treat these as an order of operations. Earlier virtues are prerequisites for later ones.

### Working (as opposed to incomplete)
- Keep the codebase in a working state at all times.
- Prove it works *recently* via automated tests; do not rely on “it should work.”
- Treat lint/format/security checks as part of “Working”, not optional polish.
- Before proposing a commit/PR, run `./check` and `./run_tests`.
- If `ruff` (or any check) fails, fix it immediately and re-run `./run_tests` after the fix.
- If you break something, stop and fix it before continuing.

### Unique (as opposed to duplicated)
- Preserve a Single Point of Truth (SPOT): each fact/algorithm should have one authoritative definition.
- Remove duplication by extracting shared logic (functions/modules/helpers) rather than copying.
- When de-duplicating, keep behavior identical and covered by tests.

### Simple (as opposed to complicated)
- Reduce local complexity: fewer operations, operands, and execution paths.
- Prefer small functions with straightforward control flow.
- When faced with complexity, split responsibilities and name intermediate concepts.

### Clear (as opposed to puzzling)
- Optimize for the next maintainer: readable names, idiomatic patterns, and consistent style.
- Make intent obvious; avoid cleverness.
- Keep related concepts together; avoid “reverse engineering” requirements.

### Easy (as opposed to difficult)
- Optimize for change: structure code so new features and fixes are easy to introduce.
- Prefer designs that localize changes and minimize ripple effects.
- Reduce incidental coupling; inject/stub dependencies to enable safe modification.

### Developed (as opposed to primitive)
- Avoid primitive obsession: introduce domain-focused types/abstractions where they simplify usage.
- Move operations to the place they belong (data + behavior together when appropriate).
- Create a small, expressive “DSL” for the problem domain when it improves clarity and ease.

### Brief (as opposed to chatty)
- Prefer concise, high signal-to-noise code.
- Remove unnecessary ceremony, repetition, and boilerplate.
- Do not sacrifice clarity for brevity; “brief” must not become “cryptic.”

## 2) Tests must be FIRST (Pragmatic Programmers)
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
- Avoid “tests” that only exercise code without checking results.

### Timely
- Prefer writing tests first (TDD) or at least alongside the production code change.
- Treat tests as “specifications by example” that document behavior.
- Let tests shape better APIs (names, parameter lists, seams for dependencies).

## 3) Refactoring safety rule
- Refactor only with a passing test baseline.
- After each small refactor, re-run tests to confirm the code remains Working.

## 4) Canonical script entrypoints (prefer scripts over ad-hoc commands)
- Use executable scripts in the repository root as the default workflow entrypoints.
- Before running raw `uv run ...` commands, check whether a dedicated script exists.
- If a project script exists for the task, use it unless the user explicitly asks for a raw command.
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
- `./fixup`: experimental auto-fix/format/upgrade pass (opt-in; review changes carefully).
- `colors_def.sh`: shared shell utility sourced by scripts; not a direct workflow entrypoint.

## 5) Wrapper precedence for validation workflows
- Do not replace `./run_tests` with direct `uv run pytest` for standard validation.
- Do not replace `./check` with separate ad-hoc tool calls for standard validation.
- Prefer wrapper scripts to preserve project flags, behavior, and conventions.
- After each change, run `./run_tests`; before commit/PR, run both `./check` and `./run_tests`.

## 6) Mutation-analysis helpers (`scripts/mutant*`)
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

