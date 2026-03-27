"""
Export results to results/ directory with pivot tables and summaries.

Usage:
    uv run python export_results.py
    uv run python export_results.py --input output/all_results.json
"""
import argparse
import json
from pathlib import Path

import pandas as pd

TASK_ORDER = [
    "nl2alloy", "nl2alloy_guided", "nl2alloy_agent", "nl2alloy_reflect",
    "alloy2alloy", "alloy2alloy_guided", "alloy2alloy_agent", "alloy2alloy_reflect",
    "sketch2alloy", "sketch2alloy_guided", "sketch2alloy_agent", "sketch2alloy_reflect",
]

REFLECT_SHORT = {
    "nl2alloy_reflect":     "NL+R",
    "alloy2alloy_reflect":  "A2A+R",
    "sketch2alloy_reflect": "SKT+R",
}

TASK_SHORT = {
    "nl2alloy":             "NL",
    "nl2alloy_guided":      "NL+G",
    "nl2alloy_agent":       "NL+A",
    "alloy2alloy":          "A2A",
    "alloy2alloy_guided":   "A2A+G",
    "alloy2alloy_agent":    "A2A+A",
    "sketch2alloy":         "SKT",
    "sketch2alloy_guided":  "SKT+G",
    "sketch2alloy_agent":   "SKT+A",
    "nl2alloy_reflect":     "NL+R",
    "alloy2alloy_reflect":  "A2A+R",
    "sketch2alloy_reflect": "SKT+R",
}

DOMAIN_ORDER = ["graph", "relation", "social_network", "production_line", "trash"]


def load(path: Path) -> pd.DataFrame:
    with open(path) as f:
        return pd.DataFrame(json.load(f))


def summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """High-level pass rate per model × task."""
    tasks = [t for t in TASK_ORDER if t in df["task_type"].unique()]
    rows = []
    for task in tasks:
        sub = df[df["task_type"] == task]
        total = len(sub)
        passed = sub["passed"].sum()
        rows.append({
            "task": task,
            "short": TASK_SHORT.get(task, task),
            "total": total,
            "passed": int(passed),
            "failed": int(total - passed),
            "pass_rate_%": round(passed / total * 100, 1) if total else 0,
        })
    return pd.DataFrame(rows)


def pivot_by_property(df: pd.DataFrame) -> pd.DataFrame:
    """Rows = properties, columns = task variants, values = Pass/Fail."""
    tasks = [t for t in TASK_ORDER if t in df["task_type"].unique()]
    pivot = (
        df.groupby(["task_id", "task_type"])["passed"]
        .max()  # pass if any trial passed (here n=1 so it's the single result)
        .unstack("task_type")
        .reindex(columns=tasks)
    )
    pivot.columns = [TASK_SHORT.get(c, c) for c in pivot.columns]
    pivot = pivot.map(lambda v: "PASS" if v else "FAIL")
    return pivot


def pivot_rates_by_domain(df: pd.DataFrame) -> pd.DataFrame:
    """Pass rate per domain × task."""
    # infer domain from task_id prefix when domain col missing
    if "domain" not in df.columns:
        return pd.DataFrame()

    tasks = [t for t in TASK_ORDER if t in df["task_type"].unique()]
    rows = []
    for domain in df["domain"].unique():
        for task in tasks:
            sub = df[(df["domain"] == domain) & (df["task_type"] == task)]
            if sub.empty:
                continue
            total = len(sub)
            passed = sub["passed"].sum()
            rows.append({
                "domain": domain,
                "task": TASK_SHORT.get(task, task),
                "total": total,
                "passed": int(passed),
                "pass_rate_%": round(passed / total * 100, 1),
            })
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    return result.pivot(index="domain", columns="task", values="pass_rate_%").reindex(
        columns=[TASK_SHORT[t] for t in tasks if TASK_SHORT[t] in
                 [TASK_SHORT.get(tt, tt) for tt in tasks]]
    )


def error_summary(df: pd.DataFrame) -> pd.DataFrame:
    failed = df[~df["passed"]]
    return (
        failed.groupby(["task_type", "error"])
        .size()
        .reset_index(name="count")
        .assign(task=lambda x: x["task_type"].map(lambda t: TASK_SHORT.get(t, t)))
        .drop(columns="task_type")
        [["task", "error", "count"]]
        .sort_values(["task", "count"], ascending=[True, False])
        .reset_index(drop=True)
    )


def markdown_summary(summary: pd.DataFrame) -> str:
    lines = [
        "# Results Summary",
        "",
        "| Task | Short | Passed | Failed | Total | Pass Rate |",
        "|------|-------|-------:|-------:|------:|----------:|",
    ]
    for _, r in summary.iterrows():
        lines.append(
            f"| {r['task']} | {r['short']} | {r['passed']} | {r['failed']} | {r['total']} | {r['pass_rate_%']}% |"
        )
    total_passed = summary["passed"].sum()
    total_all = summary["total"].sum()
    overall = round(total_passed / total_all * 100, 1)
    lines += [
        f"| **TOTAL** | | **{total_passed}** | **{int(total_all - total_passed)}** | **{total_all}** | **{overall}%** |",
        "",
        "## Task Key",
        "| Short | Full name |",
        "|-------|-----------|",
    ]
    for full, short in TASK_SHORT.items():
        lines.append(f"| {short} | {full} |")
    return "\n".join(lines)


def markdown_pivot(pivot: pd.DataFrame) -> str:
    cols = list(pivot.columns)
    header = "| Property | " + " | ".join(cols) + " |"
    sep = "|---|" + "|".join(["---"] * len(cols)) + "|"
    lines = [header, sep]
    for prop, row in pivot.iterrows():
        cells = " | ".join(
            ("✓" if v == "PASS" else "✗") for v in row
        )
        lines.append(f"| {prop} | {cells} |")
    return "\n".join(lines)


def _df_to_md(df: pd.DataFrame) -> str:
    """Render a DataFrame as a GitHub-flavored markdown table (no tabulate needed)."""
    cols = list(df.columns)
    header = "| " + " | ".join(str(c) for c in cols) + " |"
    sep = "|" + "|".join("---" for _ in cols) + "|"
    rows = []
    for _, r in df.iterrows():
        rows.append("| " + " | ".join(str(v) for v in r) + " |")
    return "\n".join([header, sep] + rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="output/all_results.json")
    args = parser.parse_args()

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    df = load(Path(args.input))
    print(f"Loaded {len(df)} results, {df['passed'].sum()} passed")

    # ── CSVs ────────────────────────────────────────────────────────────────
    summary = summary_table(df)
    summary.to_csv(results_dir / "summary.csv", index=False)
    print(f"  summary.csv ({len(summary)} rows)")

    pivot = pivot_by_property(df)
    pivot.to_csv(results_dir / "by_property.csv")
    print(f"  by_property.csv ({len(pivot)} properties × {len(pivot.columns)} tasks)")

    err = error_summary(df)
    err.to_csv(results_dir / "errors.csv", index=False)
    print(f"  errors.csv ({len(err)} rows)")

    domain_pivot = pivot_rates_by_domain(df)
    if not domain_pivot.empty:
        domain_pivot.to_csv(results_dir / "by_domain.csv")
        print(f"  by_domain.csv ({len(domain_pivot)} domains)")

    # ── Markdown report ─────────────────────────────────────────────────────
    md_lines = [markdown_summary(summary), "", "---", "", "## Pass / Fail by Property", ""]
    md_lines.append(markdown_pivot(pivot))

    if not domain_pivot.empty:
        md_lines += ["", "---", "", "## Pass Rate (%) by Domain", ""]
        md_lines.append(_df_to_md(domain_pivot.reset_index()))

    md_lines += ["", "---", "", "## Error Breakdown", ""]
    md_lines.append(_df_to_md(err))

    report = "\n".join(md_lines)
    (results_dir / "report.md").write_text(report)
    print(f"  report.md")

    # ── Console summary ──────────────────────────────────────────────────────
    print()
    print(summary.to_string(index=False))
    total_p = summary["passed"].sum()
    total_t = summary["total"].sum()
    print(f"\nOVERALL: {total_p}/{total_t} = {round(total_p/total_t*100,1)}%")


if __name__ == "__main__":
    main()
