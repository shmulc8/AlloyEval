# Replicating: _On the Effectiveness of LLMs in Writing Alloy Formulas_

Single-notebook replication of Hong, Jiang, Fu & Khurshid (2025).

## Structure

```
alloy-replication/
├── replication.ipynb          # The entire experiment in one notebook
├── requirements.txt
├── .env                       # API keys (create this yourself)
├── data/
│   ├── graph_properties.jsonl     # 3 graph properties (DAG, Cycle, Circular)
│   └── relation_properties.jsonl  # 8 relation properties (Connex, Reflexive, …)
└── output/                    # Created at runtime (results, .als files, figures)
```

## Quick Start

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...        # optional
```

Ensure the **Alloy CLI** is on your PATH (or set `ALLOY_PATH` in the notebook config cell).

Then open `replication.ipynb` and run all cells.

## The 11 Properties

| #   | Property      | Domain   | Signature                     |
| --- | ------------- | -------- | ----------------------------- |
| 1   | DAG           | graph    | `sig Node { link: set Node }` |
| 2   | Cycle         | graph    | `sig Node { link: set Node }` |
| 3   | Circular      | graph    | `sig Node { link: set Node }` |
| 4   | Connex        | relation | `sig S { r: set S }`          |
| 5   | Reflexive     | relation | `sig S { r: set S }`          |
| 6   | Symmetric     | relation | `sig S { r: set S }`          |
| 7   | Transitive    | relation | `sig S { r: set S }`          |
| 8   | Antisymmetric | relation | `sig S { r: set S }`          |
| 9   | Irreflexive   | relation | `sig S { r: set S }`          |
| 10  | Functional    | relation | `sig S { r: set S }`          |
| 11  | Function      | relation | `sig S { r: set S }`          |

## Three Tasks

1. **NL → Alloy** — translate natural language description to Alloy formula
2. **Alloy → Alloy** — generate a logically equivalent alternative formula
3. **Sketch → Alloy** — fill holes (`_`) in an incomplete formula

## Validation

Uses the Alloy Analyzer's SAT solver to check `candidate iff canonical` within a bounded scope. UNSAT = formulas are equivalent = pass.
