"""
Core experiment runner: iterate over models × tasks × properties × trials.
"""
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from .alloy import build_alloy_file, check_alloy
from .config import LLM_CONFIGS, NUM_SOLUTIONS, OUTPUT_DIR
from .data import Property, TrialResult
from .llm import TASK_CONFIGS, clean_formula, make_client, query_llm


def run_experiment(
    properties: list[Property],
    llm_configs: list[dict] = LLM_CONFIGS,
    task_names: Optional[list[str]] = None,
    num_solutions: int = NUM_SOLUTIONS,
    save_als: bool = True,
) -> list[TrialResult]:
    """Run the full experiment and return all trial results."""
    if task_names is None:
        task_names = list(TASK_CONFIGS.keys())

    OUTPUT_DIR.mkdir(exist_ok=True)

    all_results: list[TrialResult] = []
    total = len(llm_configs) * len(task_names) * len(properties) * num_solutions
    pbar = tqdm(total=total, desc="Running experiment")

    for cfg in llm_configs:
        model_name = cfg["name"]
        client = make_client(cfg)
        model_id = cfg["model"]

        for task_name in task_names:
            prompt_fn = TASK_CONFIGS[task_name]["prompt_fn"]

            for prop in properties:
                user_prompt = prompt_fn(prop)

                for trial_idx in range(num_solutions):
                    pbar.set_postfix_str(f"{model_name}/{task_name}/{prop.task_id}/#{trial_idx}")

                    raw = query_llm(client, model_id, user_prompt)
                    formula = clean_formula(raw)

                    passed, error = False, "No formula generated"
                    if formula:
                        als_content = build_alloy_file(prop, formula)
                        debug_path: Optional[Path] = None
                        if save_als:
                            debug_path = (
                                OUTPUT_DIR / model_name / task_name
                                / f"{prop.task_id}_sol{trial_idx}.als"
                            )
                        passed, error = check_alloy(als_content, debug_path)

                    all_results.append(TrialResult(
                        task_id=prop.task_id,
                        model=model_name,
                        task_type=task_name,
                        trial_idx=trial_idx,
                        raw_response=raw,
                        cleaned_formula=formula,
                        passed=passed,
                        error=error,
                    ))
                    pbar.update(1)

    pbar.close()
    return all_results
