from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_result(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def render_text_report(result: dict[str, Any]) -> str:
    lines = [
        f"Model: {result['model']}",
        f"Dataset: {result['dataset']}",
        f"Prompt: {result['prompt_version']}",
        f"Total: {result['total']}",
        f"Accuracy: {format_percent(result['accuracy'])}",
        f"Invalid responses: {result['invalid_response_count']} "
        f"({format_percent(result['invalid_response_rate'])})",
    ]

    for breakdown_name, values in result.get("breakdowns", {}).items():
        lines.append("")
        lines.append(f"By {breakdown_name}:")
        for key, accuracy in sorted(values.items()):
            lines.append(f"  {key}: {format_percent(accuracy)}")

    return "\n".join(lines)
