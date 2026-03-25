#!/usr/bin/env python3
"""Export FastAPI OpenAPI schema for frontend SDK generation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.main import app  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export OpenAPI schema from FastAPI app."
    )
    parser.add_argument(
        "--output",
        default="frontend/openapi/openapi.json",
        help="Output file path for openapi json.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = Path(args.output)
    if not output.is_absolute():
        output = (Path.cwd() / output).resolve()

    output.parent.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()
    output.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"OpenAPI schema exported: {output}")


if __name__ == "__main__":
    main()
