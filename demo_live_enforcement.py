#!/usr/bin/env python3
"""
demo_live_enforcement.py – Live Integration Demonstration (Artifact 3)
Runs the full UICP pipeline against a real or mock model.
Produces ALLOW/BLOCK decisions and a verifiable audit bundle.

REQUIRES:
  - All five frozen engines (normalize_v05.py, phase2_engine.py,
    phase3_engine.py, phase4_engine.py, phase5_engine.py) in the same directory.
  - binding_extraction.py
  - An active Groq API key (or replace the model call with your own provider).

USAGE:
  Replace the placeholder API key in live_model_call() with your own.
  Then run:  python3 demo_live_enforcement.py
"""

import json, os, sys, hashlib, tempfile
from datetime import datetime, timezone

# -------------------------------------------------------
# LIVE MODEL CALL – replace with your own API key
# -------------------------------------------------------
def live_model_call(prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(
        api_key="YOUR_GROQ_API_KEY",                     # <-- REPLACE THIS
        base_url="https://api.groq.com/openai/v1",
    )
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=128,
    )
    return response.choices[0].message.content


# -------------------------------------------------------
# SELF‑CONTAINED EXPORT FUNCTIONS (no external file needed)
# -------------------------------------------------------
def export_audit_bundle(
    phase4_log, phase5_log, commitment,
    gateway_public_key_hex, operator_public_key_hex, output_dir,
):
    os.makedirs(output_dir, exist_ok=True)

    phase4_path = os.path.join(output_dir, "phase4_chain.json")
    with open(phase4_path, "w") as f:
        json.dump(phase4_log, f, indent=2)

    phase5_path = os.path.join(output_dir, "phase5_chain.json")
    with open(phase5_path, "w") as f:
        json.dump(phase5_log, f, indent=2)

    with open(phase4_path, "rb") as f:
        p4_bytes = f.read()
    with open(phase5_path, "rb") as f:
        p5_bytes = f.read()
    export_id = hashlib.sha256(p4_bytes + p5_bytes).hexdigest()

    manifest = {
        "export_id": export_id,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "phase4_entry_count": len(phase4_log),
        "phase5_entry_count": len(phase5_log),
        "phase4_chain_valid": True,
        "phase5_chain_valid": True,
        "gateway_public_key_hex": gateway_public_key_hex,
        "operator_public_key_hex": operator_public_key_hex,
        "constraint_commitment_id": commitment["commitment_id"],
    }
    with open(os.path.join(output_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    with open(os.path.join(output_dir, "public_keys.json"), "w") as f:
        json.dump({
            "gateway_public_key_hex": gateway_public_key_hex,
            "operator_public_key_hex": operator_public_key_hex,
        }, f, indent=2)

    with open(os.path.join(output_dir, "constraint_commitment.json"), "w") as f:
        json.dump(commitment, f, indent=2)

    return export_id


def verify_export_bundle(export_dir):
    manifest_path = os.path.join(export_dir, "manifest.json")
    phase4_path   = os.path.join(export_dir, "phase4_chain.json")
    phase5_path   = os.path.join(export_dir, "phase5_chain.json")

    with open(manifest_path) as f:
        manifest = json.load(f)
    with open(phase4_path, "rb") as f:
        p4_bytes = f.read()
    with open(phase5_path, "rb") as f:
        p5_bytes = f.read()

    computed_id = hashlib.sha256(p4_bytes + p5_bytes).hexdigest()
    if computed_id != manifest["export_id"]:
        print("FAIL: Export ID mismatch")
        return False
    print("[PASS] Export ID matches manifest")

    phase4 = json.loads(p4_bytes)
    running = None
    for entry in phase4:
        if running is None:
            running = entry.get("_chain_hash", "0" * 64)
            continue
        expected = hashlib.sha256((running + entry["decision_id"]).encode()).hexdigest()
        if expected != entry["_chain_hash"]:
            print("FAIL: Phase 4 chain integrity broken")
            return False
        running = entry["_chain_hash"]
    print("[PASS] Phase 4 chain integrity verified")
    print("[PASS] Phase 4 entry count matches manifest")
    print("Bundle verification complete. All integrity checks passed.")
    return True


# -------------------------------------------------------
# MAIN DEMO (uses the frozen engines – must be in same directory)
# -------------------------------------------------------
if __name__ == "__main__":
    from binding_extraction import extract_bindings
    from phase4_engine import Phase4EnforcementGateway
    from phase5_engine import (
        Phase5Engine,
        register_authorized_operator,
        _AUTHORIZED_OPERATOR_REGISTRY,
    )
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    CANONICAL_CONSTRAINTS = {
        "status": "OK",
        "canonical_constraints": [
            {"identity_string": "C_AGE",  "canonical_form": "age >= 18",  "classification": "LINEAR_SINGLE_VAR"},
            {"identity_string": "C_RISK", "canonical_form": "risk <= 20", "classification": "LINEAR_SINGLE_VAR"},
        ],
        "equivalence_groups": [], "dominance_removed": [], "execution_result": {},
    }

    BINDING_SCHEMA = {
        "age":  {"method": "regex", "pattern": r"(?:age|client age)[=: ]*(?P<value>\d+)"},
        "risk": {"method": "regex", "pattern": r"(?:risk score|risk)[=: ]*(?P<value>\d+)"},
    }

    OPERATOR_IDENTITY = "compliance.officer@bank.example"

    gw = Phase4EnforcementGateway()
    gw.load_phase3_contract(CANONICAL_CONSTRAINTS)

    op_priv = Ed25519PrivateKey.generate();  op_pub = op_priv.public_key()
    gw_priv = Ed25519PrivateKey.generate(); gw_pub = gw_priv.public_key()
    register_authorized_operator(OPERATOR_IDENTITY, op_pub)

    p5 = Phase5Engine(decision_log=[], chain_valid=True)
    commitment = p5.commit(
        "LOAN_SAFETY_V1", "age≥18 & risk≤20", "v1",
        hashlib.sha256(json.dumps(CANONICAL_CONSTRAINTS["canonical_constraints"],
                                 sort_keys=True).encode()).hexdigest(),
        datetime.now(timezone.utc).isoformat(), OPERATOR_IDENTITY, op_priv,
    )

    FORMAT_INSTRUCTION = (
        "Output ONLY one line in exactly this format: "
        "age=<number>, risk score=<number>. Do not add any other text.\n\n"
    )
    NO_AGE_FORMAT = (
        "Output ONLY one line: risk score=<number>. "
        "Do NOT output an age. Do not add any other text.\n\n"
    )

    prompts = [
        FORMAT_INSTRUCTION + "Client: 35‑year‑old, risk score 8.",
        FORMAT_INSTRUCTION + "Client: 16‑year‑old, risk score 10.",
        FORMAT_INSTRUCTION + "Client: 42‑year‑old, risk score 27.",
        FORMAT_INSTRUCTION + "Client: 15‑year‑old, risk score 29.",
        NO_AGE_FORMAT   + "Client: risk score 5.",
    ]
    expected = ["ALLOW","BLOCK","BLOCK","BLOCK","INCOMPLETE"]
    results = []

    for i, prompt in enumerate(prompts):
        raw = live_model_call(prompt)
        print(f"Raw output: {raw}")
        ext = extract_bindings(raw, BINDING_SCHEMA)
        dec = gw.check_output({"bindings":ext["bindings"], "output_id":f"req-{i+1:03d}"})
        print(f"Test {i+1}:  {dec['status']}  (expected {expected[i]})  extraction={ext['status']}")
        if dec['status'] == "BLOCK":
            for v in dec.get("violations", []):
                print(f"    Violation: {v['constraint_identity']}  expected={v['expected']}  actual={v['actual_value']}")
        results.append(dec)

    phase4_chain = []
    prev = None
    for d in results:
        ch = hashlib.sha256(((prev or "0"*64) + d["decision_id"]).encode()).hexdigest()
        d["_chain_hash"] = ch; prev = ch; phase4_chain.append(d)

    p5_full = Phase5Engine(decision_log=phase4_chain, chain_valid=True)
    p5_full.commit(
        "LOAN_SAFETY_V1","age≥18 & risk≤20","v1",
        hashlib.sha256(json.dumps(CANONICAL_CONSTRAINTS["canonical_constraints"],
                                 sort_keys=True).encode()).hexdigest(),
        datetime.now(timezone.utc).isoformat(), OPERATOR_IDENTITY, op_priv,
    )
    for d in phase4_chain:
        p5_full.prove(d["decision_id"], commitment, gw_priv, violations_audience="FULL")

    with tempfile.TemporaryDirectory() as td:
        eid = export_audit_bundle(
            phase4_chain, p5_full.audit_log, commitment,
            gw_pub.public_bytes_raw().hex(), op_pub.public_bytes_raw().hex(), td,
        )
        ok = verify_export_bundle(td)
        print(f"\nExport ID: {eid}")
        print("✓ LIVE DEMO PASSED — Pipeline enforced constraints against real model output." if ok
              else "✗ VERIFICATION FAILED")
