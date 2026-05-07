#!/usr/bin/env python3
"""
phase5_public.py – Public Phase 5 interface.
Imports the internal trust and audit engine and exposes only the validated
runtime contract. No internal algorithms are revealed.
"""
import sys
import json

import phase5_engine as _engine


class PublicTrustEngine:
    """Public wrapper around the Phase 5 trust and audit engine."""

    def __init__(self, decision_log: list, chain_valid: bool):
        self._engine = _engine.Phase5Engine(decision_log, chain_valid)

    def commit(self, objective_id, objective_description, constraint_set_version,
               constraint_set_hash, committed_at, committed_by, operator_private_key):
        return self._engine.commit(
            objective_id=objective_id, objective_description=objective_description,
            constraint_set_version=constraint_set_version,
            constraint_set_hash=constraint_set_hash,
            committed_at=committed_at, committed_by=committed_by,
            operator_private_key=operator_private_key,
        )

    def prove(self, decision_id, commitment, gateway_private_key,
              violations_audience="REDACTED"):
        return self._engine.prove(
            decision_id=decision_id, commitment=commitment,
            gateway_private_key=gateway_private_key,
            violations_audience=violations_audience,
        )

    def override(self, original_decision_id, override_type, override_reason,
                 authorized_by, operator_private_key, timestamp, expires_at=None):
        return self._engine.override(
            original_decision_id=original_decision_id,
            override_type=override_type, override_reason=override_reason,
            authorized_by=authorized_by, operator_private_key=operator_private_key,
            timestamp=timestamp, expires_at=expires_at,
        )

    def verify_commitment(self, commitment, operator_public_key):
        return self._engine.verify_commitment(commitment, operator_public_key)

    def verify_proof(self, proof, gateway_public_key, commitment,
                     decision_record, operator_public_key):
        return self._engine.verify_proof(
            proof, gateway_public_key, commitment, decision_record,
            operator_public_key,
        )

    def verify_override(self, override):
        return self._engine.verify_override(override)

    @property
    def audit_log(self):
        return self._engine.audit_log

    @property
    def audit_chain_valid(self):
        return self._engine.audit_chain_valid
