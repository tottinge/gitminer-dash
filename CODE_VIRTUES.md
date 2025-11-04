# Code Virtues Reference

## Industrial Logic's 7 Code Virtues

These virtues are ordered by importance - earlier virtues take precedence over later ones.

### 1. Working (vs. Incomplete)
**Most important.** Code must run and produce correct results.
- Assembled, integrated, and executable
- Observed running and behaving as intended
- Proven to work recently (not just "worked once")
- Automated tests provide confidence it still works after changes
- Code that works today > code that may work someday

### 2. Unique (vs. Duplicated)
**Single Point of Truth (SPOT).** Eliminate duplication.
- Also known as: DRY (Don't Repeat Yourself), OAOO (Once and Only Once)
- No implicitly shared algorithms, strings, data structures, or numeric values
- Each concept expressed once and only once
- Working code with duplication is still burdensome and dangerous

### 3. Simple (vs. Complicated)
**Objective structural simplicity.** Minimize operations, operands, and paths.
- Fewer variables = more simple
- Fewer computation steps = more simple
- Fewer logical paths = more simple
- Example: `isPopulated(x)` is simpler than `!isEmpty(x)` (one less operator)
- Example: `isFull(x)` is simpler than `x->lastUsed < x->lastAvailable`
- Simplicity is LOCAL - doesn't matter if called function is complex

### 4. Clear (vs. Puzzling)
**First subjective virtue.** Code that teammates can understand.
- Idiomatic expressions are clearer to experienced developers
- What matters: clarity to those who share the codebase daily
- Local names are consistent with naming in the codebase, and with other names in the same scope.

### 5. Easy (vs. Difficult)
**Ease of change, not ease of reading.**
- Can you add a feature in 15 minutes vs. days?
- How quickly can you reshape code to meet new needs?
- Organization that facilitates adding/removing functionality
- Related to but distinct from Clear, Unique, Simple, Developed

### 6. Developed (vs. Primitive)
**Proper abstractions, avoiding primitive obsession.**
- Primitives (int, string, bool) give way to domain concepts
- Example: 7 integers (year, month, day...) → Date class
- Groups of operations → classes or utility libraries
- System becomes its own Domain-Specific Language
- Makes code simpler, easier, and clearer
- Single Point of Truth for domain operations

### 7. Brief (vs. Chatty)
**Concise expression of concepts.**
- `x = 5 * 10` better than `x=10; x=x+10; x=x+10; x=x+10; x=x+10;`
- Say what you mean, once
- Eliminate unnecessary ceremony and repetition
- Don't confuse brevity with obscurity
- Don't use many lines where a one-line expression still clearly states intention.

---

## Additional Code Quality Virtues (Complementary)

These virtues from our codebase analysis complement the Industrial Logic virtues:

### Cohesion
**Single Responsibility.** Each module/class/function has one clear purpose.
- Classes shouldn't be "god objects" mixing multiple concerns
- Functions should do one thing well
- Related: Simple, Easy, Developed

### Locality
**Minimize coupling.** Don't reach deep into object structures.
- Avoid chains like `obj.field.subfield.method()`
- Keep knowledge of structure local
- Related: Easy, Developed

### Consistency
**Uniform approaches.** Same problems solved the same way.
- Consistent naming conventions
- Consistent patterns (e.g., error handling, datetime usage)
- Makes code more Clear and Easy

### Encapsulation
**Hide implementation details.** Don't leak internal structure.
- Return abstractions, not implementation types
- Don't expose mutable state unnecessarily
- Related: Developed, Easy

---

## Using These Virtues in Code Reviews

1. **Prioritize by order** - Working > Unique > Simple > Clear > Easy > Developed > Brief
2. **Be specific** - Reference which virtue and why
3. **Be objective where possible** - Simple, Unique are measurable
4. **Consider context** - Clear and Easy are subjective but not arbitrary
5. **Remember**: All virtues serve the goal of maintainable, changeable code
