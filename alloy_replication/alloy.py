"""
Alloy analyzer integration: build .als files and validate formulas via CLI.
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from .config import ALLOY_PATH, ALLOY_SCOPE, ALLOY_TIMEOUT, OUTPUT_DIR
from .data import Property


def build_alloy_file(prop: Property, candidate_formula: str) -> str:
    """Build a complete .als file that checks equivalence of a candidate formula
    against the canonical ground truth using `iff`."""
    return (
        f"/* Auto-generated validation for {prop.task_id} */\n\n"
        f"{prop.signatures}\n\n"
        f"pred {prop.predicate_name} {{\n"
        f"\t{candidate_formula}\n"
        f"}}\n\n"
        f"check {prop.predicate_name} {{\n"
        f"    {prop.predicate_name} iff ({prop.canonical_formula})\n"
        f"}} for {ALLOY_SCOPE}\n"
    )


def check_alloy(
    als_content: str,
    debug_path: Optional[Path] = None,
) -> tuple[bool, Optional[str]]:
    """Run the Alloy analyzer on .als content and return (passed, error_msg).

    Returns:
        (True, None)   — UNSAT: no counterexample, formulas are equivalent
        (False, msg)   — SAT, syntax/type error, timeout, or other failure
    """
    # Use output/tmp/ (absolute) to avoid macOS /tmp symlink issues with Java
    tmp_dir = (OUTPUT_DIR / "tmp").resolve()
    tmp_dir.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(suffix=".als", dir=tmp_dir)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(als_content)

        if debug_path:
            debug_path.parent.mkdir(parents=True, exist_ok=True)
            debug_path.write_text(als_content)

        # Unique output dir per run so alloy never refuses to overwrite
        out_dir = tmp_dir / Path(tmp_path).stem

        # JDK_JAVA_OPTIONS suppresses Java module access warnings (macOS)
        env = {**os.environ, "JDK_JAVA_OPTIONS": "--enable-native-access=ALL-UNNAMED"}

        result = subprocess.run(
            [ALLOY_PATH, "exec", "--type", "text", "-o", str(out_dir), "-f", tmp_path],
            capture_output=True,
            text=True,
            timeout=ALLOY_TIMEOUT,
            env=env,
        )

        stderr = result.stderr  # alloy prints UNSAT/SAT progress to stderr

        if result.returncode != 0:
            if "Type error" in stderr:
                return False, "Type Error"
            if "Syntax error" in stderr:
                return False, "Syntax Error"
            return False, f"Unknown: {stderr[:200]}"

        if "UNSAT" in stderr:
            return True, None
        if "SAT" in stderr:
            return False, "Counterexample"
        return False, f"Unknown output: {stderr[:200]}"

    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except FileNotFoundError:
        return False, f"Alloy CLI not found at '{ALLOY_PATH}'"
    except Exception as e:
        return False, str(e)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
