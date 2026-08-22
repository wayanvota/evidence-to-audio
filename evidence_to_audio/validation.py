from __future__ import annotations

import json
import re
from pathlib import Path


URL_PATTERN = re.compile(r"https?://\S+")
MARKDOWN_HEADING_PATTERN = re.compile(r"^\s{0,3}#{1,6}\s+", re.MULTILINE)
MARKDOWN_LIST_PATTERN = re.compile(r"^\s*(?:[-*+] |\d+[.)] )", re.MULTILINE)


def validate_run(run_dir: str | Path) -> list[str]:
    root = Path(run_dir).resolve()
    errors: list[str] = []
    for required in ("manifest.json", "critic.md", "draft-script.txt", "script.txt"):
        path = root / required
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"Missing or empty {required}")

    scouts_dir = root / "scouts"
    scouts = list(scouts_dir.glob("*.md")) if scouts_dir.is_dir() else []
    if len(scouts) < 2:
        errors.append("Run must contain at least two scout reports")

    manifest_path = root / "manifest.json"
    script_path = root / "script.txt"
    if manifest_path.is_file() and script_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append("manifest.json is not valid JSON")
        else:
            script = script_path.read_text(encoding="utf-8")
            words = len(script.split())
            try:
                max_minutes = int(manifest["max_minutes"])
                words_per_minute = int(manifest["target_words_per_minute"])
            except (KeyError, TypeError, ValueError):
                errors.append("manifest is missing valid runtime settings")
            else:
                ceiling = max_minutes * words_per_minute
                if words > ceiling:
                    errors.append(f"Script has {words} words; ceiling is {ceiling}")
            if manifest.get("script_words") != words:
                errors.append("manifest script_words does not match script.txt")
            if URL_PATTERN.search(script):
                errors.append("Spoken script contains a URL; move URLs to show notes")
            if MARKDOWN_HEADING_PATTERN.search(script):
                errors.append(
                    "Spoken script contains a Markdown heading; use an audible section announcement"
                )
            if MARKDOWN_LIST_PATTERN.search(script):
                errors.append(
                    "Spoken script contains Markdown list syntax; use spoken ordinals in separate paragraphs"
                )
    return errors
