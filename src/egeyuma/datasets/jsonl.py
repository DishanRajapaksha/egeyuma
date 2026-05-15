from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from egeyuma.datasets.schema import MCQItem


class DatasetValidationError(Exception):
    """Raised when a dataset cannot be parsed into the canonical schema."""


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                yield json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise DatasetValidationError(
                    f"{path}:{line_number}: invalid JSON: {exc.msg}"
                ) from exc


def load_mcq_jsonl(path: Path) -> list[MCQItem]:
    items: list[MCQItem] = []
    for line_number, raw in enumerate(read_jsonl(path), start=1):
        try:
            items.append(MCQItem.model_validate(raw))
        except ValidationError as exc:
            raise DatasetValidationError(f"{path}:{line_number}: {exc}") from exc
    return items


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
