# Replicating and Extending: _On the Effectiveness of LLMs in Writing Alloy Formulas_

Replication and extension of Hong, Jiang, Fu & Khurshid (arXiv:2502.15441, 2025), evaluating LLMs on Alloy formal specification tasks.

**Key results:** Gemini 2.5 Pro achieves 100% on sketch completion and 95--100% on formula equivalence, comparable to the original study's o3-mini and DeepSeek R1. Guided prompting and compiler feedback improve the weaker Flash Lite model by up to 24 percentage points.

See [`report/report.md`](report/report.md) for the full write-up.

---

## Prerequisites

### Alloy Analyzer

This experiment requires the [Alloy Analyzer](https://alloytools.org/) CLI to validate generated formulas. The runner calls it for every trial to check equivalence with the canonical solution.

**macOS (Homebrew):**
```bash
brew install alloy-analyzer
```

**Other platforms:** Download from [alloytools.org](https://alloytools.org/download.html) and ensure the `alloy` binary is on your `PATH`. Requires Java 11+.

Verify it works:
```bash
alloy --version
```

### Vertex AI API Key

You need a Google Cloud Vertex AI API key to call Gemini models. Create one in the [Google Cloud Console](https://console.cloud.google.com/) under APIs & Services > Credentials.

```bash
cp .env.example .env
# Edit .env and add your key:
# VERTEX_API_KEY=your-key-here
```

### Python Dependencies

```bash
uv sync
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
