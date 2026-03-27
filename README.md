# AlloyEval

Evaluation benchmark for LLM-based Alloy formal specification generation. Replicates and extends Hong et al. (arXiv:2502.15441, 2025) with additional task variants and properties from [Alloy4Fun](https://alloy4fun.inesctec.pt/).

**Key results:** Gemini 2.5 Pro achieves 100% on sketch completion and 95--100% on formula equivalence, comparable to the original study's o3-mini and DeepSeek R1. Guided prompting and compiler feedback improve the weaker Flash Lite model by up to 24 percentage points.

See [`report/report.md`](report/report.md) for the full write-up.

---

## Prerequisites

### Alloy Analyzer

The [Alloy Analyzer](https://alloytools.org/) CLI is required to validate generated formulas against canonical solutions.

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

### Quick test

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
| `--expand` | off | Include extended dataset (30 Alloy4Fun properties) |

---

## Benchmark

**Base (11 properties):** From the original study — 3 graph properties (DAG, Cycle, Circular) and 8 relation properties (Reflexive, Symmetric, Transitive, etc.).

**Extended (30 properties):** From [Alloy4Fun](https://alloy4fun.inesctec.pt/) exercises across 4 domains: graph, social network, production line, and trash/filesystem. These have more complex signature structures (up to 6 sigs with inheritance).

**Tasks (12 variants):** 3 base tasks x 4 modes:

| Mode | Description |
|---|---|
| **Base** | nl2alloy, alloy2alloy, sketch2alloy (replicates original study) |
| **Guided** | + Alloy language reference in system prompt |
| **Agent** | + 1 round of Alloy compiler error feedback |
| **Reflect** | + 1 round of LLM self-critique (no compiler) |

---

## References

- Hong, F., Jiang, M., Fu, C., & Khurshid, S. (2025). _On the Effectiveness of LLMs in Writing Alloy Formulas._ arXiv:2502.15441.
- Macedo, N., Cunha, A., et al. (2019). _Sharing and Learning Alloy on the Web._ arXiv:1907.02275.
- Jackson, D. (2012). _Software Abstractions: Logic, Language, and Analysis._ MIT Press.
