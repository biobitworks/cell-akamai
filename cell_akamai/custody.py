"""Addressable local FCO/FCG projection. Does not claim portfolio admission or MMR commitment."""
from __future__ import annotations
from .kinetics import content_digest


def make_fco(kind: str, content: dict, context: dict) -> dict:
    content_id = content_digest({"kind": kind, "content": content})
    occurrence_id = content_digest({"content_id": content_id, "context": context})
    return {"schema": "cell_akamai.fco_projection.v1", "kind": kind,
            "content_id": content_id, "occurrence_id": occurrence_id,
            "content": content, "context": context,
            "admission_state": "UNADMITTED_LOCAL_PROJECTION"}


def make_edge(src: dict, dst: dict, rel: str) -> dict:
    allowed = {"observed_in", "derived_from", "evaluates", "produced_by", "has_sample"}
    if rel not in allowed:
        raise ValueError("Undeclared edge type: " + rel)
    return {"schema": "cell_akamai.fcg_projection.v1",
            "src": src["occurrence_id"], "dst": dst["occurrence_id"],
            "relationship": rel, "semantics": "DECLARED_NOT_CAUSAL"}
