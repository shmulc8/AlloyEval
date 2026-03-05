"""
Analysis helpers: pass@k estimator, summary tables, CSV export, plots.
"""
from dataclasses import asdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import NUM_SOLUTIONS, OUTPUT_DIR
from .data import Property, TrialResult
from .llm import TASK_CONFIGS


def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased pass@k estimator (Chen et al., 2021): 1 - C(n-c, k) / C(n, k)."""
    if n - c < k:
        return 1.0
    return float(1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1)))


def compute_pass_at_k_table(
    df: pd.DataFrame,
    k_values: list[int] = (1, 5, 10),
) -> pd.DataFrame:
    rows = []
    for (model, task_type, task_id), grp in df.groupby(["model", "task_type", "task_id"]):
        n = len(grp)
        c = int(grp["passed"].sum())
        row = {"model": model, "task_type": task_type, "task_id": task_id, "n": n, "c": c}
        for k in k_values:
            if k <= n:
                row[f"pass@{k}"] = pass_at_k(n, c, k)
        rows.append(row)
    return pd.DataFrame(rows)


def analyze_and_save(
    results: list[TrialResult],
    properties: list[Property],
    output_dir: Path = OUTPUT_DIR,
    num_solutions: int = NUM_SOLUTIONS,
) -> None:
    """Compute summary stats, save CSVs and plots to output_dir."""
    output_dir.mkdir(exist_ok=True)
    df = pd.DataFrame([asdict(r) for r in results])

    # ── Summary tables ─────────────────────────────────────────────────────
    summary = (
        df.groupby(["model", "task_type"])
        .agg(total=("passed", "count"), passed=("passed", "sum"))
        .assign(rate=lambda x: (x["passed"] / x["total"] * 100).round(1))
    )
    detail = (
        df.groupby(["model", "task_type", "task_id"])
        .agg(total=("passed", "count"), passed=("passed", "sum"))
        .assign(rate=lambda x: (x["passed"] / x["total"] * 100).round(1))
    )

    k_values = [k for k in [1, 5, 10] if k <= num_solutions]
    pak = compute_pass_at_k_table(df, k_values)
    pak_summary = (
        pak.groupby(["model", "task_type"])[[f"pass@{k}" for k in k_values]]
        .mean()
        .round(3)
    )

    error_counts = (
        df[~df["passed"]]
        .groupby(["model", "task_type", "error"])
        .size()
        .reset_index(name="count")
        .sort_values(["model", "task_type", "count"], ascending=[True, True, False])
    )
    diversity = (
        df[df["passed"]]
        .groupby(["model", "task_type", "task_id"])["cleaned_formula"]
        .nunique()
        .reset_index(name="unique_correct")
    )

    # ── Console output ─────────────────────────────────────────────────────
    print("\n── Overall Success Rates ──")
    print(summary.to_string())
    print("\n── Average Pass@k ──")
    print(pak_summary.to_string())

    # ── CSV export ─────────────────────────────────────────────────────────
    summary.to_csv(output_dir / "summary_by_model_task.csv")
    detail.to_csv(output_dir / "detail_by_property.csv")
    pak_summary.to_csv(output_dir / "pass_at_k_summary.csv")
    error_counts.to_csv(output_dir / "error_breakdown.csv", index=False)
    diversity.to_csv(output_dir / "diversity.csv", index=False)
    print(f"\nCSVs saved to {output_dir}/")

    # ── Bar chart: success rate by model × property per task ───────────────
    prop_order = [p.task_id for p in properties]
    fig, axes = plt.subplots(1, len(TASK_CONFIGS), figsize=(5 * len(TASK_CONFIGS), 5), sharey=True)
    if len(TASK_CONFIGS) == 1:
        axes = [axes]
    for ax, (task_name, cfg) in zip(axes, TASK_CONFIGS.items()):
        task_df = df[df["task_type"] == task_name]
        if task_df.empty:
            continue
        pivot = (
            task_df.groupby(["task_id", "model"])["passed"]
            .mean()
            .unstack("model")
            .reindex(prop_order)
            .dropna(how="all")
            * 100
        )
        pivot.plot.bar(ax=ax, rot=45)
        ax.set_title(cfg["label"])
        ax.set_ylabel("Success Rate (%)")
        ax.set_ylim(0, 105)
        ax.legend(title="Model")
    plt.tight_layout()
    plt.savefig(output_dir / "success_rates.png", dpi=150, bbox_inches="tight")
    plt.close()

    # ── Heatmap: pass@1 per property ───────────────────────────────────────
    if "pass@1" in pak.columns:
        fig, axes = plt.subplots(
            1, len(TASK_CONFIGS), figsize=(5 * len(TASK_CONFIGS), 6), sharey=True
        )
        if len(TASK_CONFIGS) == 1:
            axes = [axes]
        im = None
        for ax, (task_name, cfg) in zip(axes, TASK_CONFIGS.items()):
            task_pak = pak[pak["task_type"] == task_name]
            if task_pak.empty:
                continue
            heatmap_data = (
                task_pak.pivot(index="task_id", columns="model", values="pass@1")
                .reindex(prop_order)
                .dropna(how="all")
            )
            im = ax.imshow(heatmap_data.values, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
            ax.set_xticks(range(len(heatmap_data.columns)))
            ax.set_xticklabels(heatmap_data.columns, rotation=45, ha="right")
            ax.set_yticks(range(len(heatmap_data.index)))
            ax.set_yticklabels(heatmap_data.index)
            ax.set_title(cfg["label"])
            for i in range(len(heatmap_data.index)):
                for j in range(len(heatmap_data.columns)):
                    val = heatmap_data.values[i, j]
                    if not np.isnan(val):
                        ax.text(j, i, f"{val:.0%}", ha="center", va="center", fontsize=9)
        if im is not None:
            fig.colorbar(im, ax=axes, shrink=0.6, label="pass@1")
        plt.tight_layout()
        plt.savefig(output_dir / "pass_at_1_heatmap.png", dpi=150, bbox_inches="tight")
        plt.close()

    print(f"Plots saved to {output_dir}/")
