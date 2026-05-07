#!/usr/bin/env python3
"""
verify_phase3_claims.py – External Adversarial Phase 3 Verification
Uses the PUBLIC phase3_public interface ONLY.
No internal algorithms are exposed.

VALIDATED: Colab 2025‑05‑07 — 17/17 PASS, ALL CLAIMS VALIDATED.
"""
import json
from phase3_public import phase3_verify


PASS, FAIL = 0, 0


def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"[PASS] {name}")
    else:
        FAIL += 1
        print(f"[FAIL] {name}  —  {detail}")
    if detail and condition:
        print(f"       {detail}")


print("=" * 70)
print("PHASE 3 — EXTERNAL ADVERSARIAL VALIDATION SUITE")
print("=" * 70)

# ------------------------------------------------------------------
# CLAIM 1 — SINGLE‑VARIABLE PASS‑THROUGH
# ------------------------------------------------------------------
print("\n--- CLAIM 1: Single‑Variable Pass‑Through ---")
tv1 = {
    "status": "OK",
    "reduced_constraints": [
        {
            "identity_string": '[">",["var","x"],["int",5]]',
            "var": "x",
            "op": ">",
            "value": 5,
        }
    ],
    "equivalence_groups": [],
    "dominance_removed": [],
    "execution_result": {},
}
r1 = phase3_verify(tv1)
test("Status OK", r1["status"] == "OK")
test("Identity preserved",
     r1["canonical_constraints"][0]["identity_string"] == '[">",["var","x"],["int",5]]')
test("Classification LINEAR_SINGLE_VAR",
     r1["canonical_constraints"][0]["classification"] == "LINEAR_SINGLE_VAR")
test("Canonical form x >= 6",
     r1["canonical_constraints"][0]["canonical_form"] == "x >= 6")

# ------------------------------------------------------------------
# CLAIM 2 — MULTI‑VARIABLE REDUNDANCY ELIMINATION
# ------------------------------------------------------------------
print("\n--- CLAIM 2: Multi‑Variable Redundancy ---")
tv2 = {
    "status": "OK",
    "reduced_constraints": [
        {
            "identity_string": '[">",["+",["var","x"],["var","y"]],["int",10]]',
            "type": "OUT_OF_SCOPE",
            "reason": "multi-variable",
            "coeffs": {"x": 1, "y": 1},
            "op": ">",
            "value": 10,
        },
        {
            "identity_string": '[">",["var","x"],["int",6]]',
            "var": "x",
            "op": ">",
            "value": 6,
        },
        {
            "identity_string": '[">",["var","y"],["int",4]]',
            "var": "y",
            "op": ">",
            "value": 4,
        },
    ],
    "equivalence_groups": [],
    "dominance_removed": [],
    "execution_result": {},
}
r2 = phase3_verify(tv2)
test("Status OK", r2["status"] == "OK")
test("All 3 identities present",
     all(ident in [c["identity_string"] for c in r2["canonical_constraints"]]
         for ident in ['[">",["+",["var","x"],["var","y"]],["int",10]]',
                       '[">",["var","x"],["int",6]]',
                       '[">",["var","y"],["int",4]]']))
dom_weak = [d["weaker_identity"] for d in r2.get("dominance_removed", [])]
test("x+y>10 removed as redundant",
     '[">",["+",["var","x"],["var","y"]],["int",10]]' in dom_weak)
active_ids = [c["identity_string"] for c in r2.get("canonical_constraints", [])
              if c.get("classification") in ("LINEAR_SINGLE_VAR", "LINEAR_MULTI_VAR")
              and "Redundant" not in c.get("reason", "")]
test("Only x>6 and y>4 remain active",
     set(active_ids) == {'[">",["var","x"],["int",6]]', '[">",["var","y"],["int",4]]'})

# ------------------------------------------------------------------
# CLAIM 3 — MULTI‑VARIABLE CONFLICT
# ------------------------------------------------------------------
print("\n--- CLAIM 3: Multi‑Variable Conflict ---")
tv3 = {
    "status": "OK",
    "reduced_constraints": [
        {
            "identity_string": '[">",["+",["var","x"],["var","y"]],["int",10]]',
            "type": "OUT_OF_SCOPE",
            "coeffs": {"x": 1, "y": 1},
            "op": ">",
            "value": 10,
        },
        {
            "identity_string": '["<",["+",["var","x"],["var","y"]],["int",5]]',
            "type": "OUT_OF_SCOPE",
            "coeffs": {"x": 1, "y": 1},
            "op": "<",
            "value": 5,
        },
    ],
    "equivalence_groups": [],
    "dominance_removed": [],
    "execution_result": {},
}
r3 = phase3_verify(tv3)
test("CONFLICT status", r3["status"] == "CONFLICT")
test("execution_result is null", r3["execution_result"] is None)
all_cf_ids = set()
for cf in r3.get("conflicts", []):
    all_cf_ids.update(cf["constraint_identities"])
test("Both identities in conflict",
     '[">",["+",["var","x"],["var","y"]],["int",10]]' in all_cf_ids and
     '["<",["+",["var","x"],["var","y"]],["int",5]]' in all_cf_ids)

# ------------------------------------------------------------------
# CLAIM 4 — NONLINEAR PRESERVATION
# ------------------------------------------------------------------
print("\n--- CLAIM 4: Nonlinear Preservation ---")
tv4 = {
    "status": "OK",
    "reduced_constraints": [
        {
            "identity_string": '[">",["*",["var","x"],["var","y"]],["int",10]]',
            "type": "OUT_OF_SCOPE",
            "reason": "nonlinear",
        }
    ],
    "equivalence_groups": [],
    "dominance_removed": [],
    "execution_result": {},
}
r4 = phase3_verify(tv4)
test("Status OK", r4["status"] == "OK")
test("Identity preserved",
     r4["canonical_constraints"][0]["identity_string"] == '[">",["*",["var","x"],["var","y"]],["int",10]]')
test("Classification NONLINEAR",
     r4["canonical_constraints"][0]["classification"] == "NONLINEAR")

# ------------------------------------------------------------------
# CLAIM 5 — DETERMINISM
# ------------------------------------------------------------------
print("\n--- CLAIM 5: Determinism ---")
tv5 = {
    "status": "OK",
    "reduced_constraints": [
        {
            "identity_string": '[">",["+",["var","x"],["var","y"]],["int",10]]',
            "type": "OUT_OF_SCOPE",
            "coeffs": {"x": 1, "y": 1},
            "op": ">",
            "value": 10,
        },
        {
            "identity_string": '[">",["var","x"],["int",6]]',
            "var": "x",
            "op": ">",
            "value": 6,
        },
        {
            "identity_string": '[">",["var","y"],["int",4]]',
            "var": "y",
            "op": ">",
            "value": 4,
        },
    ],
    "equivalence_groups": [],
    "dominance_removed": [],
    "execution_result": {},
}
r5a = json.dumps(phase3_verify(json.loads(json.dumps(tv5))), sort_keys=True, default=str)
r5b = json.dumps(phase3_verify(json.loads(json.dumps(tv5))), sort_keys=True, default=str)
test("Two runs produce identical JSON", r5a == r5b)

# ------------------------------------------------------------------
# CLAIM 6 — IDENTITY LEDGER COMPLETENESS
# ------------------------------------------------------------------
print("\n--- CLAIM 6: Identity Ledger ---")
tv6 = {
    "status": "OK",
    "reduced_constraints": [
        {
            "identity_string": '[">",["var","a"],["int",1]]',
            "var": "a",
            "op": ">",
            "value": 1,
        },
        {
            "identity_string": '["<",["var","b"],["int",100]]',
            "var": "b",
            "op": "<",
            "value": 100,
        },
        {
            "identity_string": '[">",["*",["var","a"],["var","b"]],["int",0]]',
            "type": "OUT_OF_SCOPE",
            "reason": "nonlinear",
        },
        {
            "identity_string": '[">=",["+",["var","a"],["var","b"]],["int",50]]',
            "type": "OUT_OF_SCOPE",
            "coeffs": {"a": 1, "b": 1},
            "op": ">=",
            "value": 50,
        },
    ],
    "equivalence_groups": [],
    "dominance_removed": [],
    "execution_result": {},
}
r6 = phase3_verify(tv6)
in_ids = [c["identity_string"] for c in tv6["reduced_constraints"]]
out_ids = [c["identity_string"] for c in r6.get("canonical_constraints", [])]
test("All input identities present", all(i in out_ids for i in in_ids))
test("No extra identities invented", set(out_ids) == set(in_ids))

print("\n" + "=" * 70)
print(f"RESULTS: {PASS} passed, {FAIL} failed")
if FAIL == 0:
    print("VERDICT: ALL CLAIMS VALIDATED — Phase 3 is externally proven.")
else:
    print(f"VERDICT: {FAIL} failure(s) — claims violated.")
print("=" * 70)
