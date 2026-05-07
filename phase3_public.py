#!/usr/bin/env python3
"""
phase3_public.py – Public Phase 3 interface.
Imports the internal engine and only exposes the validated output contract.
No internal algorithms are revealed.

VALIDATED: Colab 2025‑05‑07 — 17/17 PASS, ALL CLAIMS VALIDATED.
"""
import sys
import json

import phase3_engine as _engine


def phase3_verify(phase2_output: dict) -> dict:
    """
    Public Phase 3 entry point.

    Parameters:
        phase2_output:  The exact JSON output produced by a conformant
                        Phase 2 implementation (v1.1 or later).

    Returns:
        The Phase 3 output contract:
        {
          "status": "OK" | "CONFLICT" | "REJECTED",
          "canonical_constraints": [...],
          "equivalence_groups": [...],
          "dominance_removed": [...],
          "execution_result": {...} | null
        }
    """
    result = _engine.phase3(phase2_output)
    return result
