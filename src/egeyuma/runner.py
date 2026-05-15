from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from egeyuma.datasets.jsonl import load_mcq_jsonl, write_json
from egeyuma.models import create_model_adapter
from egeyuma.prompts import render_mcq_prompt
from egeyuma.scorers import extract_choice, is_correct


def _accuracy(correct: int, total: int) -> float:
    return correct / total if total else 0.0


def _build_breakdowns(items: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    fields = ["subject", "domain", "difficulty", "language_style"]
    breakdowns: dict[str, dict[str, float]] = {}

    for field in fields:
        totals: dict[str, int] = defaultdict(int)
        correct: dict[str, int] = defaultdict(int)
        for item in items:
            key = str(item.get(field) or "unknown")
            totals[key] += 1
            correct[key] += int(bool(item["correct"]))
        breakdowns[field] = {key: _accuracy(correct[key], total) for key, total in totals.items()}

    return breakdowns


def run_mcq_evaluation(
    *,
    dataset_path: Path,
    model_name: str,
    prompt_name: str,
    output_path: Path,
) -> dict[str, Any]:
    dataset = load_mcq_jsonl(dataset_path)
    model = create_model_adapter(model_name)

    result_items: list[dict[str, Any]] = []
    correct_count = 0
    invalid_count = 0

    for item in dataset:
        prompt = render_mcq_prompt(item, prompt_name)
        response = model.generate(prompt)
        prediction = extract_choice(response.raw_response)
        correct = is_correct(prediction, item.answer_label)

        correct_count += int(correct)
        invalid_count += int(prediction is None)

        result_items.append(
            {
                "id": item.id,
                "gold": item.answer_label,
                "prediction": prediction,
                "raw_response": response.raw_response,
                "correct": correct,
                "subject": item.subject,
                "domain": item.domain,
                "difficulty": item.difficulty,
                "language_style": item.language_style,
                "source": item.source,
            }
        )

    payload: dict[str, Any] = {
        "run_id": datetime.now(UTC).isoformat(),
        "framework": "egeyuma",
        "engine": "native-scaffold",
        "model": model_name,
        "task": "mcq",
        "dataset": str(dataset_path),
        "prompt_version": prompt_name,
        "total": len(dataset),
        "correct": correct_count,
        "accuracy": _accuracy(correct_count, len(dataset)),
        "invalid_response_count": invalid_count,
        "invalid_response_rate": _accuracy(invalid_count, len(dataset)),
        "breakdowns": _build_breakdowns(result_items),
        "items": result_items,
    }

    write_json(output_path, payload)
    return payload
