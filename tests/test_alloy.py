import pytest
from pathlib import Path
from alloy_replication.data import load_properties
from alloy_replication.alloy import build_alloy_file, check_alloy

DATA_DIR = Path("data")


@pytest.fixture(scope="module")
def properties():
    return (
        load_properties(DATA_DIR / "graph_properties.jsonl")
        + load_properties(DATA_DIR / "relation_properties.jsonl")
    )


@pytest.fixture(scope="module")
def dag(properties):
    return next(p for p in properties if p.task_id == "DAG")


@pytest.fixture(scope="module")
def reflexive(properties):
    return next(p for p in properties if p.task_id == "Reflexive")


class TestBuildAlloyFile:
    def test_contains_pred(self, dag):
        als = build_alloy_file(dag, dag.canonical_formula)
        assert "pred DAG" in als

    def test_contains_check(self, dag):
        als = build_alloy_file(dag, dag.canonical_formula)
        assert "check DAG" in als
        assert "iff" in als

    def test_contains_formula(self, dag):
        als = build_alloy_file(dag, dag.canonical_formula)
        assert dag.canonical_formula in als

    def test_contains_signatures(self, dag):
        als = build_alloy_file(dag, dag.canonical_formula)
        assert dag.signatures in als


class TestCheckAlloy:
    def test_canonical_passes(self, dag):
        ok, err = check_alloy(build_alloy_file(dag, dag.canonical_formula))
        assert ok is True
        assert err is None

    def test_all_canonicals_pass(self, properties):
        for p in properties:
            ok, err = check_alloy(build_alloy_file(p, p.canonical_formula))
            assert ok is True, f"{p.task_id} canonical failed: {err}"

    def test_wrong_formula_fails(self, reflexive):
        # Negation of the canonical should produce a counterexample
        ok, err = check_alloy(build_alloy_file(reflexive, "no x: S | x in x.R"))
        assert ok is False

    def test_syntax_error(self, dag):
        ok, err = check_alloy(build_alloy_file(dag, "this is not valid alloy syntax %%%"))
        assert ok is False
        assert err in ("Syntax Error", "Type Error")

    def test_empty_formula(self, dag):
        # Empty pred body — trivially satisfiable, likely counterexample
        ok, err = check_alloy(build_alloy_file(dag, ""))
        assert ok is False
