"""
Entry point for the Alloy LLM replication experiment.

Usage:
    uv run python run_experiment.py                          # paper replication (3 tasks)
    uv run python run_experiment.py --fast                   # quick run: gemini-3.1-flash-lite, 1 solution
    uv run python run_experiment.py --guide                  # + guided variants
    uv run python run_experiment.py --agent                  # + agent variants (Alloy feedback)
    uv run python run_experiment.py --reflect                # + reflect variants (self-critique, no Alloy)
    uv run python run_experiment.py --expand                 # + extended properties
    uv run python run_experiment.py --solutions 2 --workers 16
"""
import argparse
import json
from dataclasses import asdict

from alloy_replication.alloy import build_alloy_file, check_alloy
from alloy_replication.analysis import analyze_and_save
from alloy_replication.config import DATA_DIR, GEMINI_FLASH_PREVIEW_CONFIG, LLM_CONFIGS, NUM_SOLUTIONS, OUTPUT_DIR
from alloy_replication.data import load_all_extended_properties, load_properties
from alloy_replication.experiment import run_experiment

_BASE_TASKS = ["nl2alloy", "alloy2alloy", "sketch2alloy"]
_GUIDED_TASKS = ["nl2alloy_guided", "alloy2alloy_guided", "sketch2alloy_guided"]
_AGENT_TASKS = ["nl2alloy_agent", "alloy2alloy_agent", "sketch2alloy_agent"]
_REFLECT_TASKS = ["nl2alloy_reflect", "alloy2alloy_reflect", "sketch2alloy_reflect"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--solutions", type=int, default=NUM_SOLUTIONS,
        help="Number of LLM samples per property per task (default: %(default)s)",
    )
    parser.add_argument(
        "--workers", type=int, default=32,
        help="Parallel worker threads for LLM calls (default: %(default)s)",
    )
    parser.add_argument(
        "--expand", action="store_true",
        help="Also run on extended dataset (data/extended/): graph, social_network, "
             "production_line, trash domains (nl2alloy + alloy2alloy only)",
    )
    parser.add_argument(
        "--guide", action="store_true",
        help="Include guided task variants (Alloy reference in system prompt)",
    )
    parser.add_argument(
        "--agent", action="store_true",
        help="Include agent task variants (iterative Alloy feedback, up to 5 rounds)",
    )
    parser.add_argument(
        "--reflect", action="store_true",
        help="Include reflect task variants (iterative self-critique, no Alloy feedback)",
    )
    parser.add_argument(
        "--fast", action="store_true",
        help="Quick run: use gemini-3.1-flash-preview with 1 solution per property",
    )
    args = parser.parse_args()

    if args.fast:
        if args.solutions == NUM_SOLUTIONS:  # not explicitly overridden
            args.solutions = 1

    llm_configs = list(LLM_CONFIGS)
    if args.fast:
        llm_configs = [GEMINI_FLASH_PREVIEW_CONFIG]

    task_names = list(_BASE_TASKS)
    if args.guide:
        task_names += _GUIDED_TASKS
    if args.agent:
        task_names += _AGENT_TASKS
    if args.reflect:
        task_names += _REFLECT_TASKS

    # ── Load data ──────────────────────────────────────────────────────────
    properties = (
        load_properties(DATA_DIR / "graph_properties.jsonl")
        + load_properties(DATA_DIR / "relation_properties.jsonl")
    )
    if args.expand:
        extended = load_all_extended_properties(DATA_DIR / "extended")
        print(f"Loaded {len(properties)} paper properties + {len(extended)} extended properties")
        properties = properties + extended
    else:
        print(f"Loaded {len(properties)} properties: {[p.task_id for p in properties]}")
    print(f"Models: {[c['name'] for c in llm_configs]}")
    print(f"Tasks: {task_names}")
    print(f"Solutions per property per task: {args.solutions}")
    print(f"Workers: {args.workers}")

    # ── Smoke test: canonical formula must validate against itself ─────────
    p = properties[0]
    ok, err = check_alloy(build_alloy_file(p, p.canonical_formula))
    print(f"Smoke test (Alloy): passed={ok}, error={err}")
    if not ok:
        raise SystemExit("ERROR: Alloy CLI not working. Check ALLOY_PATH in config.py.")

    # ── Run ────────────────────────────────────────────────────────────────
    results = run_experiment(
        properties, llm_configs,
        task_names=task_names,
        num_solutions=args.solutions,
        num_workers=args.workers,
    )

    # ── Persist raw results ────────────────────────────────────────────────
    OUTPUT_DIR.mkdir(exist_ok=True)
    results_path = OUTPUT_DIR / "all_results.json"
    with open(results_path, "w") as f:
        json.dump([asdict(r) for r in results], f, indent=2)
    print(f"\nSaved {len(results)} results → {results_path}")

    # ── Analyze ────────────────────────────────────────────────────────────
    analyze_and_save(results, properties, num_solutions=args.solutions)

    total = len(results)
    passed = sum(r.passed for r in results)
    print(f"\n{'='*60}")
    print(f" DONE — {passed}/{total} passed ({passed/total*100:.1f}%)")
    print(f"{'='*60}")
