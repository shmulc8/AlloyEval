"""
Data structures and loaders for the 11 subject Alloy specifications.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Property:
    """One of the 11 subject specifications from the paper."""
    task_id: str
    domain: str                  # "graph" or "relation"
    prompt: str                  # natural language description
    signatures: str              # Alloy sig block
    predicate_name: str
    canonical_formula: str       # ground-truth formula body
    sketch: str                  # formula with holes (_)
    sketch_hint: str             # hint about what to fill in


@dataclass
class TrialResult:
    """Result of one LLM generation + Alloy validation."""
    task_id: str
    model: str
    task_type: str               # "nl2alloy" | "alloy2alloy" | "sketch2alloy"
    trial_idx: int
    raw_response: Optional[str] = None
    cleaned_formula: Optional[str] = None
    passed: bool = False
    error: Optional[str] = None  # None | "Syntax Error" | "Type Error" | "Counterexample" | ...


def load_properties(jsonl_path: Path) -> list[Property]:
    props = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if line:
                props.append(Property(**json.loads(line)))
    return props
