#!/usr/bin/env python3
"""Run all five public verification suites in sequence."""
import subprocess, sys

scripts = [
    ("PHASE 1", "verify_phase1_claims.py"),
    ("PHASE 2", "verify_phase2_claims.py"),
    ("PHASE 3", "verify_phase3_claims.py"),
    ("PHASE 4", "verify_phase4_claims.py"),
    ("PHASE 5", "verify_phase5_claims.py"),
]

exit_code = 0
for name, script in scripts:
    print("=" * 70)
    print(f"RUNNING {name} EXTERNAL VERIFICATION …")
    print("=" * 70)
    try:
        result = subprocess.run([sys.executable, script], check=False)
        if result.returncode != 0:
            print(f"\n{name} verification exited with code {result.returncode}.")
            exit_code = 1
    except FileNotFoundError:
        print(f"\n{name} script '{script}' not found.")
        exit_code = 1
    print()

print("=" * 70)
if exit_code == 0:
    print("ALL PHASES VERIFIED — Phases 1-5 are externally proven.")
else:
    print("ONE OR MORE PHASES REPORTED FAILURES — review output above.")
print("=" * 70)
sys.exit(exit_code)
