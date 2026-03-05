"""
LLM client, response cleaning, and prompt templates for the three tasks.
"""
import os
import re
from typing import Optional

from openai import OpenAI

from .config import TEMPERATURE
from .data import Property

# ── Client ─────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are an expert in formal methods and the Alloy specification language. "
    "When asked, output ONLY the Alloy formula (the predicate body), nothing else. "
    "Do not include the pred declaration, curly braces, or any explanation."
)


def make_client(config: dict) -> OpenAI:
    kwargs: dict = {"api_key": os.getenv(config["api_key_env"], "")}
    if config.get("base_url"):
        kwargs["base_url"] = config["base_url"]
    return OpenAI(**kwargs)


def query_llm(client: OpenAI, model: str, user_prompt: str) -> Optional[str]:
    """Send a prompt and return the raw text response, or None on error."""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=512,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"  LLM error: {e}")
        return None


def clean_formula(raw: Optional[str]) -> Optional[str]:
    """Extract the Alloy formula body from an LLM response."""
    if not raw:
        return None
    text = raw.strip()
    m = re.search(r"```(?:alloy)?\s*(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    m2 = re.search(r"pred\s+\w+\s*\{(.*)\}", text, re.DOTALL)
    if m2:
        text = m2.group(1).strip()
    text = text.rstrip("}").strip()
    text = text.replace('"""', "").strip()
    return text if text else None


# ── Prompt templates ────────────────────────────────────────────────────────

def prompt_nl2alloy(prop: Property) -> str:
    """Task 1: Natural Language → Alloy."""
    return (
        f"Implement the following Alloy predicate {prop.predicate_name} "
        f"as defined in the comments:\n\n"
        f"{prop.signatures}\n"
        f"pred {prop.predicate_name} {{\n"
        f"  -- {prop.prompt}\n"
        f"}}\n\n"
        f"Output only the formula in the predicate body."
    )


def prompt_alloy2alloy(prop: Property) -> str:
    """Task 2: Alloy → Alloy (generate equivalent alternative)."""
    return (
        f"Given the following Alloy predicate:\n\n"
        f"{prop.signatures}\n"
        f"pred {prop.predicate_name} {{\n"
        f"  {prop.canonical_formula}\n"
        f"}}\n\n"
        f"Create an alternative but logically equivalent Alloy formula for this predicate.\n"
        f"Output only the formula in the predicate body."
    )


def prompt_sketch2alloy(prop: Property) -> str:
    """Task 3: Sketch → Alloy (fill holes marked with _)."""
    return (
        f"Complete the following Alloy sketch to satisfy the property described in the comments:\n\n"
        f"{prop.signatures}\n"
        f"pred {prop.predicate_name} {{\n"
        f"  -- {prop.prompt}\n"
        f"  {prop.sketch}\n"
        f"}}\n\n"
        f"Hint: {prop.sketch_hint}\n"
        f"Populate the holes (marked with _) in the sketch. "
        f"Output only the completed formula in the predicate body."
    )


TASK_CONFIGS: dict[str, dict] = {
    "nl2alloy":     {"prompt_fn": prompt_nl2alloy,     "label": "Task 1: NL \u2192 Alloy"},
    "alloy2alloy":  {"prompt_fn": prompt_alloy2alloy,  "label": "Task 2: Alloy \u2192 Alloy"},
    "sketch2alloy": {"prompt_fn": prompt_sketch2alloy, "label": "Task 3: Sketch \u2192 Alloy"},
}
