"""Write the api's OpenAPI document to a file (input to `openapi-typescript`)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from api.main import create_app


def main(output_path: str = "web/openapi.json") -> int:
    """Generate the OpenAPI JSON without starting the app."""
    schema = create_app(run_bootstrap=False).openapi()
    Path(output_path).write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
