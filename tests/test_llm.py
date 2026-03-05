import pytest
from alloy_replication.llm import clean_formula, TASK_CONFIGS
from alloy_replication.data import Property


@pytest.fixture
def prop():
    return Property(
        task_id="Reflexive",
        domain="relation",
        prompt="Every element in S is related to itself",
        signatures="sig S {}\none sig R {\n\trel: S -> S\n}",
        predicate_name="Reflexive",
        canonical_formula="all x: S | x -> x in R.rel",
        sketch="all x: S | x _ x in R.rel",
        sketch_hint="Replace _ with the correct arrow operator",
    )


class TestCleanFormula:
    def test_plain_formula(self):
        assert clean_formula("all x: S | x in x.R") == "all x: S | x in x.R"

    def test_strips_markdown_block(self):
        raw = "```alloy\nall x: S | x in x.R\n```"
        assert clean_formula(raw) == "all x: S | x in x.R"

    def test_strips_plain_code_block(self):
        raw = "```\nall x: S | x in x.R\n```"
        assert clean_formula(raw) == "all x: S | x in x.R"

    def test_strips_pred_wrapper(self):
        raw = "pred Reflexive { all x: S | x in x.R }"
        assert clean_formula(raw) == "all x: S | x in x.R"

    def test_none_input(self):
        assert clean_formula(None) is None

    def test_empty_string(self):
        assert clean_formula("") is None

    def test_whitespace_only(self):
        assert clean_formula("   ") is None


class TestTaskConfigs:
    def test_all_tasks_present(self):
        assert set(TASK_CONFIGS.keys()) == {"nl2alloy", "alloy2alloy", "sketch2alloy"}

    def test_all_have_prompt_fn(self):
        for name, cfg in TASK_CONFIGS.items():
            assert callable(cfg["prompt_fn"]), f"{name} missing prompt_fn"

    def test_nl2alloy_prompt(self, prop):
        prompt = TASK_CONFIGS["nl2alloy"]["prompt_fn"](prop)
        assert prop.predicate_name in prompt
        assert prop.prompt in prompt

    def test_alloy2alloy_prompt(self, prop):
        prompt = TASK_CONFIGS["alloy2alloy"]["prompt_fn"](prop)
        assert prop.canonical_formula in prompt

    def test_sketch2alloy_prompt(self, prop):
        prompt = TASK_CONFIGS["sketch2alloy"]["prompt_fn"](prop)
        assert prop.sketch in prompt
        assert prop.sketch_hint in prompt
