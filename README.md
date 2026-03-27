# Replicating and Extending: _On the Effectiveness of LLMs in Writing Alloy Formulas_

Replication and extension of Hong, Jiang, Fu & Khurshid (arXiv:2502.15441, 2025), evaluating LLMs on Alloy formal specification tasks.

**Key results:** Gemini 2.5 Pro achieves 100% on sketch completion and 95--100% on formula equivalence, comparable to the original study's o3-mini and DeepSeek R1. Guided prompting and compiler feedback improve the weaker Flash Lite model by up to 24 percentage points.

See [`report/report.md`](report/report.md) for the full write-up.

---

## Repository Structure

```
alloy-replication/
├── run_experiment.py              # Main CLI entry point
├── export_results.py              # Export results to CSV pivot tables
├── pyproject.toml
├── .env.example                   # API key template
│
├── alloy_replication/             # Core package
│   ├── config.py                  # Models, paths, experiment parameters
│   ├── data.py                    # Property / TrialResult dataclasses + loaders
│   ├── llm.py                     # Vertex AI client, structured output, prompts
│   ├── alloy.py                   # Alloy CLI integration (.als builder + validator)
│   ├── experiment.py              # Parallel trial runner with progress + checkpoints
│   ├── analysis.py                # pass@k, CSV export, bar charts, heatmaps
│   └── guide.py                   # Alloy language reference (for guided tasks)
│
├── data/
│   ├── graph_properties.jsonl     # 3 graph properties (DAG, Cycle, Circular)
│   ├── relation_properties.jsonl  # 8 relation properties (Connex, Reflexive, ...)
│   └── extended/                  # 30 extended properties (4 domains)
│
├── report/
│   ├── report.md                  # Full project report
│   ├── generate_figures.py        # Regenerate all figures from results
│   └── fig*.png                   # Report figures
│
└── output/                        # Created at runtime (gitignored)
```

---

## Setup

### 1. Install dependencies

```bash
uv sync
```

### 2. Install the Alloy CLI

```bash
brew install alloy-analyzer   # macOS
```

Verify: `alloy --version`

### 3. Configure API key

Copy `.env.example` to `.env` and add your Vertex AI API key:

```
VERTEX_API_KEY=your-key-here
```

---

## Running the Experiment

### Quick test (1 solution, fastest model)

```bash
uv run python run_experiment.py --fast
```

### Full experiment

```bash
uv run python run_experiment.py --guide --agent --reflect --expand --solutions 3 --workers 32
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--solutions N` | 20 | LLM samples per property per task |
| `--workers N` | 32 | Parallel worker threads |
| `--fast` | off | Use Flash Lite only, 1 solution |
| `--guide` | off | Include guided variants (Alloy reference in system prompt) |
| `--agent` | off | Include agent variants (Alloy compiler feedback, 1 retry) |
| `--reflect` | off | Include reflect variants (self-critique, 1 retry) |
| `--expand` | off | Include extended dataset (30 extra properties) |

---

## Task Variants

| Variant | Description |
|---|---|
| **Base** | Direct replication: nl2alloy, alloy2alloy, sketch2alloy |
| **Guided** | Same prompts + Alloy language reference injected into system prompt |
| **Agent** | 1 attempt + 1 round of Alloy compiler error feedback |
| **Reflect** | 1 attempt + 1 round of LLM self-critique (no compiler) |

---

## Models

| Model | Type | Notes |
|---|---|---|
| Gemini 2.5 Flash Lite | Lightweight | Fast, cheap, lower accuracy |
| Gemini 2.5 Pro | Reasoning | Near paper-level results |

All calls go through Vertex AI REST API with structured JSON output.

---

## Validation

For each generated formula, the runner builds an `.als` file and checks equivalence with the Alloy analyzer:

```alloy
check predName { predName iff (canonical_formula) } for 3
```

- **UNSAT** (no counterexample in scope 3) = **pass**
- **SAT** (counterexample found) = **fail** (Counterexample)
- Parse error = **fail** (Syntax Error / Type Error)

---

## Reference

Hong, F., Jiang, M., Fu, C., & Khurshid, S. (2025).
_On the Effectiveness of LLMs in Writing Alloy Formulas._
arXiv:2502.15441.
