"""
Core experiment runner: iterate over models × tasks × properties × trials.
Supports parallel execution via ThreadPoolExecutor (I/O-bound LLM calls).

Task variants:
  - Standard (nl2alloy / alloy2alloy / sketch2alloy): paper replication protocol.
    Sketch2alloy gets one error-feedback retry on Syntax/Type errors (§III-C).
  - Guided (_guided suffix): same prompts but with an Alloy language reference
    injected into the system prompt.
  - Agent (_agent suffix): iterative feedback loop up to AGENT_MAX_STEPS rounds,
    feeding Alloy error messages back to the LLM until the formula passes.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from .alloy import build_alloy_file, check_alloy
from .config import LLM_CONFIGS, NUM_SOLUTIONS, OUTPUT_DIR
import json
from dataclasses import asdict
from .data import Property, TrialResult
from .llm import (
    SYSTEM_PROMPT_WITH_GUIDE,
    TASK_CONFIGS,
    clean_formula,
    make_client,
    prompt_sketch2alloy_feedback,
    query_llm_with_messages,
)

# Errors that warrant a feedback retry on sketch / agent tasks
_RETRYABLE_ERRORS = {"Syntax Error", "Type Error", "Counterexample"}

# Maximum LLM rounds for agent / reflect tasks
AGENT_MAX_STEPS = 2
REFLECT_MAX_STEPS = 2


def _is_sketch_task(task_name: str) -> bool:
    return task_name == "sketch2alloy" or task_name == "sketch2alloy_guided"


def _system_prompt(task_name: str) -> Optional[str]:
    """Return override system prompt for guided tasks, else None (use default)."""
    return SYSTEM_PROMPT_WITH_GUIDE if task_name.endswith("_guided") else None


def _debug_path(model_name: str, task_name: str, prop: Property, trial_idx: int) -> Path:
    return OUTPUT_DIR / model_name / task_name / f"{prop.task_id}_sol{trial_idx}.als"


# ── Standard trial (single prompt, no feedback) ────────────────────────────

def _run_standard_trial(
    client,
    model_name: str,
    model_id: str,
    task_name: str,
    prop: Property,
    trial_idx: int,
    save_als: bool,
) -> TrialResult:
    cfg = TASK_CONFIGS[task_name]
    messages = [{"role": "user", "content": cfg["prompt_fn"](prop)}]
    sys_prompt = _system_prompt(task_name)

    raw = query_llm_with_messages(client, model_id, messages, system_prompt=sys_prompt)
    formula = clean_formula(raw)

    passed, error = False, "No formula generated"
    if formula:
        als_content = build_alloy_file(prop, formula)
        debug_path = _debug_path(model_name, task_name, prop, trial_idx) if save_als else None
        passed, error = check_alloy(als_content, debug_path)

    return TrialResult(
        task_id=prop.task_id, model=model_name, task_type=task_name,
        trial_idx=trial_idx, raw_response=raw, cleaned_formula=formula,
        passed=passed, error=error, attempts=1,
    )


# ── Sketch trial: one error-feedback retry (paper §III-C) ──────────────────

def _run_sketch_trial(
    client,
    model_name: str,
    model_id: str,
    task_name: str,
    prop: Property,
    trial_idx: int,
    save_als: bool,
) -> TrialResult:
    cfg = TASK_CONFIGS[task_name]
    sys_prompt = _system_prompt(task_name)
    messages = [{"role": "user", "content": cfg["prompt_fn"](prop)}]

    raw = query_llm_with_messages(client, model_id, messages, system_prompt=sys_prompt)
    formula = clean_formula(raw)

    passed, error, attempts = False, "No formula generated", 1
    debug_path = _debug_path(model_name, task_name, prop, trial_idx) if save_als else None

    if formula:
        passed, error = check_alloy(build_alloy_file(prop, formula), debug_path)

        # One error-feedback retry on fixable parse/type errors
        if not passed and error in {"Syntax Error", "Type Error"}:
            attempts = 2
            messages += [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": prompt_sketch2alloy_feedback(prop, error)},
            ]
            raw2 = query_llm_with_messages(client, model_id, messages, system_prompt=sys_prompt)
            formula2 = clean_formula(raw2)
            if formula2:
                passed, error = check_alloy(build_alloy_file(prop, formula2), debug_path)
                if passed:
                    raw, formula = raw2, formula2

    return TrialResult(
        task_id=prop.task_id, model=model_name, task_type=task_name,
        trial_idx=trial_idx, raw_response=raw, cleaned_formula=formula,
        passed=passed, error=error, attempts=attempts,
    )


# ── Agent trial: up to AGENT_MAX_STEPS rounds with Alloy feedback ───────────

def _run_agent_trial(
    client,
    model_name: str,
    model_id: str,
    task_name: str,
    prop: Property,
    trial_idx: int,
    save_als: bool,
) -> TrialResult:
    # Map agent task to its base prompt config
    base_task = task_name.replace("_agent", "")
    cfg = TASK_CONFIGS[base_task]
    messages = [{"role": "user", "content": cfg["prompt_fn"](prop)}]
    debug_path = _debug_path(model_name, task_name, prop, trial_idx) if save_als else None

    raw, formula = None, None
    passed, error = False, "No formula generated"

    for step in range(AGENT_MAX_STEPS):
        raw = query_llm_with_messages(client, model_id, messages)
        formula = clean_formula(raw)

        if not formula:
            error = "No formula generated"
            break

        passed, error = check_alloy(build_alloy_file(prop, formula), debug_path)

        if passed:
            break

        if step < AGENT_MAX_STEPS - 1:
            messages += [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": (
                    f"The formula you provided is incorrect. "
                    f"The Alloy checker reported: {error}\n\n"
                    f"Please analyse the error and provide a corrected formula body only."
                )},
            ]

    return TrialResult(
        task_id=prop.task_id, model=model_name, task_type=task_name,
        trial_idx=trial_idx, raw_response=raw, cleaned_formula=formula,
        passed=passed, error=error, attempts=step + 1,
    )


# ── Reflect trial: up to AGENT_MAX_STEPS rounds with LLM self-critique only ─

def _run_reflect_trial(
    client,
    model_name: str,
    model_id: str,
    task_name: str,
    prop: Property,
    trial_idx: int,
    save_als: bool,
) -> TrialResult:
    """Agent without Alloy access: LLM reviews its own formula each round."""
    base_task = task_name.replace("_reflect", "")
    cfg = TASK_CONFIGS[base_task]
    messages = [{"role": "user", "content": cfg["prompt_fn"](prop)}]
    debug_path = _debug_path(model_name, task_name, prop, trial_idx) if save_als else None

    raw, formula = None, None
    passed, error = False, "No formula generated"

    for step in range(REFLECT_MAX_STEPS):
        raw = query_llm_with_messages(client, model_id, messages)
        formula = clean_formula(raw)

        if not formula:
            error = "No formula generated"
            break

        passed, error = check_alloy(build_alloy_file(prop, formula), debug_path)

        if passed:
            break

        if step < REFLECT_MAX_STEPS - 1:
            messages += [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": (
                    "Please review your Alloy formula carefully. "
                    "Check that it correctly captures the property described, "
                    "paying attention to quantifiers, relational operators, and edge cases. "
                    "If you find any issues, provide a corrected formula body only. "
                    "Otherwise, confirm the formula is correct by repeating it."
                )},
            ]

    return TrialResult(
        task_id=prop.task_id, model=model_name, task_type=task_name,
        trial_idx=trial_idx, raw_response=raw, cleaned_formula=formula,
        passed=passed, error=error, attempts=step + 1,
    )


# ── Dispatcher ─────────────────────────────────────────────────────────────

def _run_trial(
    client,
    model_name: str,
    model_id: str,
    task_name: str,
    prop: Property,
    trial_idx: int,
    save_als: bool,
) -> TrialResult:
    if task_name.endswith("_agent"):
        return _run_agent_trial(client, model_name, model_id, task_name, prop, trial_idx, save_als)
    if task_name.endswith("_reflect"):
        return _run_reflect_trial(client, model_name, model_id, task_name, prop, trial_idx, save_als)
    if _is_sketch_task(task_name):
        return _run_sketch_trial(client, model_name, model_id, task_name, prop, trial_idx, save_als)
    return _run_standard_trial(client, model_name, model_id, task_name, prop, trial_idx, save_als)


def _needs_sketch(task_name: str) -> bool:
    """Return True if the task requires the property to have a sketch."""
    base = task_name.replace("_agent", "").replace("_guided", "").replace("_reflect", "")
    return base == "sketch2alloy"


# ── Main entry point ───────────────────────────────────────────────────────

def run_experiment(
    properties: list[Property],
    llm_configs: list[dict] = LLM_CONFIGS,
    task_names: Optional[list[str]] = None,
    num_solutions: int = NUM_SOLUTIONS,
    save_als: bool = True,
    num_workers: int = 32,
    checkpoint_every: int = 10,
) -> list[TrialResult]:
    """Run the full experiment and return all trial results.

    Results are checkpointed to output/checkpoint.json every `checkpoint_every`
    completed trials so progress is preserved on interruption.
    """
    if task_names is None:
        task_names = ["nl2alloy", "alloy2alloy", "sketch2alloy"]

    OUTPUT_DIR.mkdir(exist_ok=True)
    checkpoint_path = OUTPUT_DIR / "checkpoint.json"

    clients = {cfg["name"]: make_client(cfg) for cfg in llm_configs}
    work = [
        (cfg["name"], cfg["model"], task_name, prop, trial_idx)
        for cfg in llm_configs
        for task_name in task_names
        for prop in properties
        # Skip sketch-requiring tasks for extended properties (no sketch field)
        if not (_needs_sketch(task_name) and prop.sketch is None)
        for trial_idx in range(num_solutions)
    ]

    results: list[TrialResult] = []
    passed_count = 0
    with ThreadPoolExecutor(max_workers=num_workers) as pool:
        futures = {
            pool.submit(
                _run_trial,
                clients[model_name], model_name, model_id,
                task_name, prop, trial_idx, save_als,
            ): (model_name, task_name, prop.task_id, trial_idx)
            for model_name, model_id, task_name, prop, trial_idx in work
        }

        total = len(futures)
        with tqdm(total=total, desc="Running experiment", unit="trial") as pbar:
            for future in as_completed(futures):
                model_name, task_name, task_id, trial_idx = futures[future]
                result = future.result()
                results.append(result)
                if result.passed:
                    passed_count += 1

                pbar.set_postfix({
                    "passed": f"{passed_count}/{len(results)}",
                    "last": f"{model_name}/{task_name}/{task_id}",
                })
                pbar.update(1)

                # Checkpoint periodically
                if len(results) % checkpoint_every == 0 or len(results) == total:
                    with open(checkpoint_path, "w") as f:
                        json.dump([asdict(r) for r in results], f)

    return results
