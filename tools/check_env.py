"""Report which required environment variables are set in `.env` — names only, never values."""

from __future__ import annotations

import sys
from pathlib import Path

REQUIRED: tuple[str, ...] = (
    "APP_ENV",
    "INDEX_BACKEND",
    "QDRANT_URL",
    "QDRANT_COLLECTION",
    "STORAGE_CONNECTION_STRING",
    "BLOB_CONTAINER",
    "INGEST_QUEUE",
    "DATABASE_URL",
    "FOUNDRY_ENDPOINT",
    "FOUNDRY_API_KEY",
    "FOUNDRY_API_VERSION",
    "CHAT_PROVIDER",
    "CHAT_DEPLOYMENT",
    "JUDGE_DEPLOYMENT",
    "EMBEDDING_DEPLOYMENT",
    "EMBEDDING_DIMENSIONS",
    "ARIZE_SPACE_ID",
    "ARIZE_API_KEY",
    "ARIZE_PROJECT_NAME",
)


def parse_env_names(text: str) -> dict[str, bool]:
    """Map each variable name in a dotenv text to whether it has a non-empty value."""
    names: dict[str, bool] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        value = value.split(" #", 1)[0].strip().strip('"').strip("'")
        names[name.strip().removeprefix("export ").strip()] = bool(value)
    return names


def report(env_names: dict[str, bool]) -> tuple[list[str], int]:
    """Return printable lines and the number of missing required variables."""
    lines: list[str] = []
    missing_count = 0
    for name in REQUIRED:
        is_set = env_names.get(name, False)
        missing_count += 0 if is_set else 1
        lines.append(f"  [{'set' if is_set else 'MISSING'}] {name}")
    return lines, missing_count


def main(env_path: str = ".env") -> int:
    """Print the report; exit 1 when the file is absent or a required variable is missing."""
    path = Path(env_path)
    if not path.is_file():
        print(f"{env_path} not found: copy .env.example to .env and fill it in")
        return 1
    lines, missing_count = report(parse_env_names(path.read_text(encoding="utf-8")))
    print("\n".join(lines))
    print("All required variables are set." if missing_count == 0 else f"{missing_count} missing.")
    return 0 if missing_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
