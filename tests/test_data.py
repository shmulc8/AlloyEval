import pytest
from pathlib import Path
from alloy_replication.data import Property, TrialResult, load_properties

DATA_DIR = Path("data")


def test_load_graph_properties():
    props = load_properties(DATA_DIR / "graph_properties.jsonl")
    assert len(props) == 3
    assert all(isinstance(p, Property) for p in props)
    assert all(p.domain == "graph" for p in props)


def test_load_relation_properties():
    props = load_properties(DATA_DIR / "relation_properties.jsonl")
    assert len(props) == 8
    assert all(p.domain == "relation" for p in props)


def test_load_all_properties():
    props = (
        load_properties(DATA_DIR / "graph_properties.jsonl")
        + load_properties(DATA_DIR / "relation_properties.jsonl")
    )
    assert len(props) == 11
    ids = [p.task_id for p in props]
    assert "DAG" in ids
    assert "Reflexive" in ids


def test_property_fields():
    props = load_properties(DATA_DIR / "graph_properties.jsonl")
    p = props[0]
    assert p.task_id
    assert p.signatures
    assert p.predicate_name
    assert p.canonical_formula
    assert p.sketch
    assert p.sketch_hint


def test_trial_result_defaults():
    r = TrialResult(task_id="DAG", model="test", task_type="nl2alloy", trial_idx=0)
    assert r.passed is False
    assert r.error is None
    assert r.raw_response is None
