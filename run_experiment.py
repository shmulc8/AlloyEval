"""
Entry point for the Alloy LLM replication experiment.

Usage:
    uv run python run_experiment.py                   # full run (10 solutions)
    uv run python run_experiment.py --solutions 2     # quick test
"""
import argparse
import json
from dataclasses import asdict

from alloy_replication.alloy import build_alloy_file, check_alloy
from alloy_replication.analysis import analyze_and_save
from alloy_replication.config import DATA_DIR, LLM_CONFIGS, NUM_SOLUTIONS, OUTPUT_DIR
from alloy_replication.data import load_properties
from alloy_replication.experiment import run_experiment

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--solutions", type=int, default=NUM_SOLUTIONS,
        help="Number of LLM samples per property per task (default: %(default)s)",
    )
    args = parser.parse_args()

    # ── Load data ──────────────────────────────────────────────────────────
    properties = (
        load_properties(DATA_DIR / "graph_properties.jsonl")
        + load_properties(DATA_DIR / "relation_properties.jsonl")
    )
    print(f"Loaded {len(properties)} properties: {[p.task_id for p in properties]}")
    print(f"Models: {[c['name'] for c in LLM_CONFIGS]}")
    print(f"Solutions per property per task: {args.solutions}")

    # ── Smoke test: canonical formula must validate against itself ─────────
    p = properties[0]
    ok, err = check_alloy(build_alloy_file(p, p.canonical_formula))
    print(f"Smoke test (Alloy): passed={ok}, error={err}")
    if not ok:
        raise SystemExit("ERROR: Alloy CLI not working. Check ALLOY_PATH in config.py.")

    # ── Run ────────────────────────────────────────────────────────────────
    results = run_experiment(properties, LLM_CONFIGS, num_solutions=args.solutions)

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
