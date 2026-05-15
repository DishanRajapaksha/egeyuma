from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from egeyuma.datasets.jsonl import load_mcq_jsonl, write_json
from egeyuma.datasets.schema import MCQItem
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


def build_result_item(
    *,
    item: MCQItem,
    prediction: str | None,
    raw_response: str,
    correct: bool,
) -> dict[str, Any]:
    return {
        "id": item.id,
        "gold": item.answer_label,
        "prediction": prediction,
        "raw_response": raw_response,
        "correct": correct,
        "subject": item.subject,
        "domain": item.domain,
        "difficulty": item.difficulty,
        "language_style": item.language_style,
        "source": item.source,
    }


def build_result_payload(
    *,
    engine: str,
    dataset_path: Path,
    model_name: str,
    prompt_name: str,
    result_items: list[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    correct_count = sum(int(bool(item["correct"])) for item in result_items)
    invalid_count = sum(int(item["prediction"] is None) for item in result_items)

    payload: dict[str, Any] = {
        "run_id": datetime.now(UTC).isoformat(),
        "framework": "egeyuma",
        "engine": engine,
        "model": model_name,
        "task": "mcq",
        "dataset": str(dataset_path),
        "prompt_version": prompt_name,
        "total": len(result_items),
        "correct": correct_count,
        "accuracy": _accuracy(correct_count, len(result_items)),
        "invalid_response_count": invalid_count,
        "invalid_response_rate": _accuracy(invalid_count, len(result_items)),
        "breakdowns": _build_breakdowns(result_items),
        "items": result_items,
    }
    if metadata:
        payload["metadata"] = metadata
    return payload


def run_native_mcq_evaluation(
    *,
    dataset_path: Path,
    model_name: str,
    prompt_name: str,
    output_path: Path,
    base_url: str | None = None,
    api_key: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 16,
) -> dict[str, Any]:
    dataset = load_mcq_jsonl(dataset_path)
    model = create_model_adapter(
        model_name,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    result_items: list[dict[str, Any]] = []

    for item in dataset:
        prompt = render_mcq_prompt(item, prompt_name)
        response = model.generate(prompt)
        prediction = extract_choice(response.raw_response)
        correct = is_correct(prediction, item.answer_label)

        result_items.append(
            build_result_item(
                item=item,
                prediction=prediction,
                raw_response=response.raw_response,
                correct=correct,
            )
        )

    payload = build_result_payload(
        engine="native",
        dataset_path=dataset_path,
        model_name=model_name,
        prompt_name=prompt_name,
        result_items=result_items,
    )
    write_json(output_path, payload)
    return payload


def run_mcq_evaluation(
    *,
    dataset_path: Path,
    model_name: str,
    prompt_name: str,
    output_path: Path,
    engine: Literal["native", "inspect"] = "native",
    base_url: str | None = None,
    api_key: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 16,
) -> dict[str, Any]:
    if engine == "native":
        return run_native_mcq_evaluation(
            dataset_path=dataset_path,
            model_name=model_name,
            prompt_name=prompt_name,
            output_path=output_path,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if engine == "inspect":
        from egeyuma.inspect_runner import run_inspect_mcq_evaluation

        return run_inspect_mcq_evaluation(
            dataset_path=dataset_path,
            model_name=model_name,
            prompt_name=prompt_name,
            output_path=output_path,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    raise ValueError(f"Unsupported engine {engine!r}. Supported engines: native, inspect")
