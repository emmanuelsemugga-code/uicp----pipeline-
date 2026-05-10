
PHASE 1 – EXTERNAL ADVERSARIAL VALIDATION DOCUMENT
For engineers and AI labs to test, validate, or invalidate Phase 1 claims
This document proves the problem and the solution – without revealing the system internals.
1. THE DISEASE: REPRESENTATION INCONSISTENCY
Every system that processes constraints (rules, policies, safety bounds) faces a silent, structural failure:
Two expressions that mean exactly the same thing are treated as different objects because they look different.
This is not a bug in any particular implementation. It is a representation gap – a side effect of relying on raw string form for comparison, hashing, caching, or deduplication.
In practice:
x > 5 and 5 < x become two different hashes.
x > 5 and x > (2+3) become two different hashes.
A system built on string-level identity cannot see that these constraints are identical in meaning.
The result: silent structural misalignment – invisible to evaluation, yet capable of splitting policy paths, corrupting constraint caches, and hiding inconsistency inside multi-agent or multi-model systems.
Concrete Impact: Cache Inconsistency
Consider a caching layer that stores computation results keyed by raw constraint strings. Five different expressions of the same constraint:
x > 5
5 < x
x > (2+3)
x > 0+5
(x) > (5)
Without Phase 1, each produces a different key → 5 cache entries → 4 wasted computations.
With Phase 1, all five normalize to one canonical identity → 1 cache entry → no wasted computation.
At 10,000 evaluations per day, with 30% of constraints arriving in alternate forms, this eliminates 3,000 redundant computations per day — without changing a single line of model code.
This failure is structural. It exists in every pipeline that uses raw constraint strings for hashing, caching, or deduplication. The demos in the repository reproduce it in under 60 seconds.
LLM Input Inconsistency
The same five forms, when passed directly to an LLM, create five different prompts — each with a different SHA256. The model may reason differently about each, a known source of prompt sensitivity. Phase 1 reduces all five to a single canonical prompt, removing the structural source of inconsistency before the model ever sees it. It does not make the LLM deterministic; it removes the input drift that causes unnecessary variation.
2. WHAT PHASE 1 CLAIMS — AND WHAT IT DOES NOT
The following scope is mandatory for all external communication. Use it verbatim.
DO CLAIM:
"Phase 1 enforces consistent constraint representation — a prerequisite layer for preventing hidden misalignment."
DO NOT CLAIM:
This prevents hidden misalignment.
This makes LLMs deterministic.
This fixes hallucination.
Phase 1 removes structural ambiguity in constraint representation. It guarantees that syntactically equivalent constraints collapse to a single canonical identity. It closes the representation gap.
Phase 1 Claims
Claim
Description
Determinism
Same input → same canonical identity string and SHA256 on any conforming implementation.
Boundedness
No admitted input can cause unbounded structural growth. All outputs respect strict node, depth, variable, and compound limits.
Termination
The normalization pipeline always finishes in a single pass. No loops, no divergence.
Fixed-Point
Normalizing the output a second time produces an identical result.
Commutativity
AND(A,B) and AND(B,A) normalize to the same identity.
Absorption
Redundant forms like A OR (A AND B) are automatically reduced.
Identity Bijection
Two inputs produce the same identity if and only if they are equivalent under the defined syntactic reduction rules (constant folding, relational flipping, boolean simplification, etc.).
Phase 1 does NOT claim:
Semantic equivalence for compound expressions (e.g., x+1>6 vs x>5 – that is Phase 2 work).
Deterministic LLM outputs or hallucination prevention.
Prevention of hidden misalignment by itself.
Unbreakability.
3. HOW TO INDEPENDENTLY VALIDATE
You do not need access to the internal engine. Use the following test vectors with any standard SHA256 tool.
Test Vector 1 – Single constraint (determinism)
Input constraint: x > 5
Expected canonical identity string:
[" > ",["var","x"],["int",5]]
Expected SHA256 of that identity string (UTF-8, no spaces):
ed69b80b347eeea06915a3af43303d8997ed33cb0f05200504f1dbc18b8f5907
Test Vector 2 – Commutativity and folding (multiple forms collapse)
Input set: ["x > 5", "5 < x", "x > (2+3)", "x > 0+5", "(x) > (5)"]
Expected output: exactly one canonical identity string (the same as in Test Vector 1).
The SHA256 of the sorted, JSON-serialised list of outputs must match:
b4fb9ac22836d9bec098fa675577371521973d9e5687399e2e9b2d7dfb31df00
Test Vector 3 – Permutation invariance
Take the input set from Test Vector 2, shuffle its order, and normalize again.
The SHA256 of the sorted output list must be identical to the un-shuffled run.
Test Vector 4 – Structural bounds (boundedness)
Submit 17 constraints → must be rejected (exceeds constraint count limit, K=16).
Submit a constraint with AST depth > 32 → must be rejected.
Submit constraints using 65 distinct variables → must be rejected.
If you have a conformant Phase 1 implementation, these tests will all PASS.
Why this does not let you replicate Phase 1:
You cannot derive the canonical identity string from the raw constraint without the full pipeline. The test vectors only allow you to verify that a claimed Phase 1 output is correct. They do not teach you how to produce that output yourself.
4. INTEGRATION INTERFACE (BLACK-BOX API)
Phase 1 is designed to sit as a front gate — before any constraint reaches a model, policy engine, or verification system.
Function signature (conceptual):
NORMALIZE(constraint_set, available_vars) → {result, constraints}
Input:
constraint_set: a list of constraint strings in the DSL (e.g., ["x > 5", "x < 10"]).
available_vars: a set of variable names that are allowed (e.g., {"x"}).
Output:
On success: {result: "OK", constraints: [...]} — a sorted list of canonical identity strings (the JSON-serialized canonical ASTs).
On failure: {result: "REJECT+HALT", reason: string} — no partial output, immediate halt.
Any system that currently hashes or compares raw constraint strings can replace that step with a call to this normalization layer.
5. CHALLENGE TO ENGINEERS AND LABS
You are invited to try to break Phase 1 within its declared scope. A valid break must:
Use only the defined DSL and stay within the admission limits (≤16 constraints, depth ≤32, variables ≤64, integers within 128-bit signed range).
Produce an input where:
The output is not deterministic (two runs on the same input produce different identity strings or hashes), or
The pipeline fails to terminate or requires more than one pass, or
Two structurally equivalent inputs (under the defined syntactic rules) produce different canonical identities, or
A bounded input causes unbounded growth.
If you find such a case, you will have identified a genuine protocol flaw — and we want to know. Please provide the exact input, the expected vs. actual output, and the step where divergence occurs.
6. NO REPLICATION BARRIER
This document is intentionally incomplete for system construction. It demonstrates the existence and effect of Phase 1 but omits all internal mechanisms — the pipeline order, normalization algorithms, admission gate implementation, and transformation rules — to prevent unauthorised replication.
Phase 1’s full specification is available under controlled disclosure. The present document is for external validation only.
Verification: The full Demonstration Suite (run_all.py, demo scripts, test vectors) is available at the published repository. A single command reproduces all evidence shown here in under 60 seconds. The SHA256 test vectors are cross-language conformance targets.
End of Phase 1 External Adversarial Validation Document.
