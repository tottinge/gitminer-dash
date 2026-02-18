# Warp agent coding rules (7 Code Virtues + FIRST unit tests)
Apply these rules whenever you edit, create, or refactor code in this repo.

## 1) Prefer virtuous code (Industrial Logic: 7 Code Virtues)
Treat these as an order of operations. Earlier virtues are prerequisites for later ones.

### Working (as opposed to incomplete)
- Keep the codebase in a working state at all times.
- Prove it works *recently* via automated tests; do not rely on “it should work.”
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
