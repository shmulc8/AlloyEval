"""
Data structures and loaders for Alloy specifications.
Supports both the original 11-property paper format and the extended dataset format.
"""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Property:
    """One Alloy specification (paper or extended dataset)."""
    task_id: str
    domain: str                        # "graph", "relation", "social_network", etc.
    prompt: str                        # natural language description
    signatures: str                    # Alloy sig block
    predicate_name: str
    canonical_formula: str             # ground-truth formula body
    sketch: Optional[str] = None      # formula with holes (_); None for extended props
    sketch_hint: Optional[str] = None # hint about what to fill in; None for extended props


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
    attempts: int = 1            # sketch2alloy may use a second attempt with error feedback


def load_properties(jsonl_path: Path) -> list[Property]:
    """Load paper-format properties (original 11-property schema)."""
    props = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if line:
                props.append(Property(**json.loads(line)))
    return props


def load_extended_properties(jsonl_path: Path, domain: str = "") -> list[Property]:
    """Load extended-format properties.

    Extended format fields:
      - predicate_definition: "pred <name> {\\n..." → predicate_name extracted
      - canonical_solution:   "  <body>\\n}"       → canonical_formula extracted
      - check:                full check command    (not used at runtime)
    """
    if not domain:
        domain = jsonl_path.stem.replace("_problems", "")
    props = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            m = re.match(r"pred\s+(\w+)", raw["predicate_definition"])
            pred_name = m.group(1) if m else raw["task_id"]
            # Strip closing } from canonical_solution to get the formula body
            formula = raw["canonical_solution"].rstrip().rstrip("}").strip()
            props.append(Property(
                task_id=f"{domain}/{raw['task_id']}",
                domain=domain,
                prompt=raw["prompt"],
                signatures=raw["signatures"],
                predicate_name=pred_name,
                canonical_formula=formula,
                sketch=None,
                sketch_hint=None,
            ))
    return props


def load_all_extended_properties(extended_dir: Path) -> list[Property]:
    """Load all *.jsonl files from data/extended/."""
    props = []
    for path in sorted(extended_dir.glob("*.jsonl")):
        props.extend(load_extended_properties(path))
    return props
