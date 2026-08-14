"""One-off live smoke test for create_paper_brief OpenAI parse. Not a unit test."""
# Usage:
#   just sandbox-run "uv run python scripts/smoke_openai_call.py"
#   just sandbox-shell
#   uv run python scripts/smoke_openai_call.py
#
# Reads OPENAI_BASE_URL and OPENAI_MODEL from the project-root .env when they
# are not already in the process environment. Uses create() so invalid JSON is
# printed before Pydantic validation.
# Full text: scripts/smoke_openai_full_text.txt (same folder as this script).

from __future__ import annotations

import os
from pathlib import Path

from openai import OpenAI
from openai.lib._parsing import type_to_response_format_param
from pydantic import ValidationError

from paper_reviewer.schemas.topic_brief_generation.generate_paper_brief import (
    PaperBriefContent,
)
from paper_reviewer.topic_brief_generation.generate_paper_brief.llm import (
    build_brief_user_message,
    load_paper_brief_template,
    parse_paper_brief_content,
    resolve_openai_base_url,
    resolve_openai_model,
)

_PLACEHOLDER_API_KEY = "not-needed"
_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT_DIR = Path(__file__).resolve().parent
_FULL_TEXT_PATH = _SCRIPT_DIR / "smoke_openai_full_text.txt"


def _apply_dotenv(path: Path) -> None:
    """Fill missing process env keys from a Compose-style .env file."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


_apply_dotenv(_ROOT / ".env")

base_url = resolve_openai_base_url(
    os.environ.get("OPENAI_BASE_URL"),
    in_container=Path("/.dockerenv").exists(),
)
if base_url is None:
    raise SystemExit("OPENAI_BASE_URL is not set in the environment or .env")

model = resolve_openai_model(os.environ.get("OPENAI_MODEL"))
if model is None:
    raise SystemExit("OPENAI_MODEL is not set in the environment or .env")

api_key = os.environ.get("OPENAI_API_KEY") or _PLACEHOLDER_API_KEY
client = OpenAI(api_key=api_key, base_url=base_url)

if not _FULL_TEXT_PATH.is_file():
    raise SystemExit(f"Full text file is missing: {_FULL_TEXT_PATH}")
full_text_plain = _FULL_TEXT_PATH.read_text(encoding="utf-8").strip()
if not full_text_plain:
    raise SystemExit(f"Full text file is empty: {_FULL_TEXT_PATH}")

messages = [
    {"role": "system", "content": load_paper_brief_template()},
    {
        "role": "user",
        "content": build_brief_user_message(
            full_text_plain=full_text_plain,
            title="Dummy Outbreak Report",
            journal="Test Journal",
            published_year=2026,
        ),
    },
]

print("base_url:", base_url)
print("model:", model)
print("full_text:", _FULL_TEXT_PATH.name, f"({len(full_text_plain)} chars)")

completion = client.chat.completions.create(
    model=model,
    messages=messages,
    response_format=type_to_response_format_param(PaperBriefContent),
)

message = completion.choices[0].message
print("--- raw content ---")
print(repr(message.content))
print("--- parsed ---")
try:
    print(parse_paper_brief_content(message.content or ""))
except (ValidationError, ValueError) as exc:
    print(exc)
