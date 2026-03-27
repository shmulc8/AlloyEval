"""
LLM client, response cleaning, and prompt templates for the three tasks.
Prompt wording follows Hong, Jiang, Fu & Khurshid (arXiv:2502.15441).
"""
import json
import os
import re
import time
from typing import Optional

from google import genai
from google.genai import types

from .config import TEMPERATURE
from .data import Property
from .guide import ALLOY_GUIDE

# ── Client ─────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are an expert in formal methods and the Alloy specification language. "
    "When asked, output ONLY the Alloy formula (the predicate body), nothing else. "
    "Do not include the pred declaration, curly braces, or any explanation."
)

SYSTEM_PROMPT_WITH_GUIDE = SYSTEM_PROMPT + "\n\n" + ALLOY_GUIDE


def make_client(config: dict) -> genai.Client:
    """Create a Vertex AI client from config."""
    return genai.Client(
        api_key=os.getenv(config["api_key_env"], ""),
        vertexai=True,
    )


def query_llm(client: genai.Client, model: str, user_prompt: str) -> Optional[str]:
    """Send a single-turn prompt and return the raw text response, or None on error."""
    return query_llm_with_messages(client, model, [{"role": "user", "content": user_prompt}])


def query_llm_with_messages(
    client: genai.Client,
    model: str,
    messages: list[dict],
    max_retries: int = 5,
    system_prompt: Optional[str] = None,
) -> Optional[str]:
    """Send a multi-turn conversation via Vertex AI and return raw text, or None on error."""
    sys_msg = system_prompt if system_prompt is not None else SYSTEM_PROMPT

    # Convert OpenAI-style messages to google-genai Contents
    contents = []
    for msg in messages:
        role = "model" if msg["role"] == "assistant" else msg["role"]
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

    config = types.GenerateContentConfig(
        system_instruction=sys_msg,
        temperature=TEMPERATURE,
        max_output_tokens=2048,
        response_mime_type="application/json",
        response_schema={
            "type": "OBJECT",
            "properties": {"formula": {"type": "STRING"}},
            "required": ["formula"],
        },
    )

    delay = 20.0
    for attempt in range(max_retries):
        try:
            resp = client.models.generate_content(
                model=model, contents=contents, config=config,
            )
            return json.loads(resp.text)["formula"]
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err or "rate" in err.lower():
                if attempt < max_retries - 1:
                    m = re.search(r"retry in (\d+(?:\.\d+)?)s", err)
                    wait = float(m.group(1)) + 2 if m else delay
                    time.sleep(wait)
                    delay = min(delay * 1.5, 120)
                    continue
            print(f"  LLM error: {e}")
            return None
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
    # Remove a single trailing '}' only if braces are unbalanced (leftover pred wrapper)
    if text.count("}") > text.count("{"):
        text = text[:text.rfind("}")].strip()
    text = text.replace('"""', "").strip()
    return text if text else None


# ── Prompt templates (aligned with paper) ──────────────────────────────────

def prompt_nl2alloy(prop: Property) -> str:
    """Task 1: Natural Language → Alloy (paper: §III-A)."""
    return (
        f"Implement the following Alloy predicate {prop.predicate_name} "
        f"as defined in the comments:\n\n"
        f"{prop.signatures}\n"
        f"pred {prop.predicate_name} {{\n"
        f"  -- {prop.prompt}\n"
        f"}}\n\n"
        f"Output only the complete formula that goes inside the predicate body. "
        f"Include all quantifiers and operators — do not include the pred declaration or braces."
    )


def prompt_alloy2alloy(prop: Property) -> str:
    """Task 2: Alloy → Alloy (paper: §III-B)."""
    return (
        f"Give an Alloy formula that is equivalent to the following predicate "
        f"{prop.predicate_name}:\n\n"
        f"{prop.signatures}\n"
        f"pred {prop.predicate_name} {{\n"
        f"  {prop.canonical_formula}\n"
        f"}}\n\n"
        f"Output only the complete formula that goes inside the predicate body. "
        f"Include all quantifiers and operators — do not include the pred declaration or braces."
    )


def prompt_sketch2alloy(prop: Property) -> str:
    """Task 3: Sketch → Alloy, first attempt (paper: §III-C)."""
    return (
        f"Complete the following sketch of the Alloy predicate {prop.predicate_name} "
        f"with respect to the property defined in the comments:\n\n"
        f"{prop.signatures}\n"
        f"pred {prop.predicate_name} {{\n"
        f"  -- {prop.prompt}\n"
        f"  {prop.sketch}\n"
        f"}}\n\n"
        f"Hint: {prop.sketch_hint}\n"
        f"Output the entire completed formula (with the blank filled in), not just the missing part. "
        f"Include all quantifiers and operators — do not include the pred declaration or braces."
    )


def prompt_sketch2alloy_feedback(prop: Property, error_msg: str) -> str:
    """Task 3: Sketch → Alloy, second attempt with error feedback (paper: §III-C)."""
    return (
        f"The formula you provided produced the following error:\n\n"
        f"{error_msg}\n\n"
        f"Please fix it. Complete the following sketch of the Alloy predicate "
        f"{prop.predicate_name} with respect to the property defined in the comments:\n\n"
        f"{prop.signatures}\n"
        f"pred {prop.predicate_name} {{\n"
        f"  -- {prop.prompt}\n"
        f"  {prop.sketch}\n"
        f"}}\n\n"
        f"Hint: {prop.sketch_hint}\n"
        f"Output the entire completed formula (with the blank filled in), not just the missing part. "
        f"Include all quantifiers and operators — do not include the pred declaration or braces."
    )


TASK_CONFIGS: dict[str, dict] = {
    # ── Standard tasks (paper replication) ────────────────────────────────
    "nl2alloy":             {"prompt_fn": prompt_nl2alloy,     "label": "Task 1: NL → Alloy"},
    "alloy2alloy":          {"prompt_fn": prompt_alloy2alloy,  "label": "Task 2: Alloy → Alloy"},
    "sketch2alloy":         {"prompt_fn": prompt_sketch2alloy, "label": "Task 3: Sketch → Alloy"},
    # ── Guided variants (Alloy reference injected into system prompt) ─────
    "nl2alloy_guided":      {"prompt_fn": prompt_nl2alloy,     "label": "Task 1G: NL → Alloy (guided)",    "guided": True},
    "alloy2alloy_guided":   {"prompt_fn": prompt_alloy2alloy,  "label": "Task 2G: Alloy → Alloy (guided)", "guided": True},
    "sketch2alloy_guided":  {"prompt_fn": prompt_sketch2alloy, "label": "Task 3G: Sketch → Alloy (guided)","guided": True},
    # ── Agent variants (iterative Alloy feedback, up to 5 rounds) ─────────
    "nl2alloy_agent":       {"prompt_fn": prompt_nl2alloy,     "label": "Task 1A: NL → Alloy (agent)"},
    "alloy2alloy_agent":    {"prompt_fn": prompt_alloy2alloy,  "label": "Task 2A: Alloy → Alloy (agent)"},
    "sketch2alloy_agent":   {"prompt_fn": prompt_sketch2alloy, "label": "Task 3A: Sketch → Alloy (agent)"},
    # ── Reflect variants (iterative self-critique, no Alloy feedback) ──────
    "nl2alloy_reflect":     {"prompt_fn": prompt_nl2alloy,     "label": "Task 1R: NL → Alloy (reflect)"},
    "alloy2alloy_reflect":  {"prompt_fn": prompt_alloy2alloy,  "label": "Task 2R: Alloy → Alloy (reflect)"},
    "sketch2alloy_reflect": {"prompt_fn": prompt_sketch2alloy, "label": "Task 3R: Sketch → Alloy (reflect)"},
}
