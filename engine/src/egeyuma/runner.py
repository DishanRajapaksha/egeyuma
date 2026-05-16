from __future__ import annotations

import os
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Any, Literal

from egeyuma.datasets.jsonl import load_mcq_jsonl, write_json
from egeyuma.datasets.schema import MCQItem
from egeyuma.logging import LogFn, null_log
from egeyuma.models import create_model_adapter
from egeyuma.prompts import load_prompt_template, render_mcq_prompt
from egeyuma.scorers import extract_choice, is_correct

SCHEMA_VERSION = "1.1.0"
ANSWER_LABELS = tuple("ABCDE")


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


def _failure_category(*, prediction: str | None, raw_response: str, correct: bool) -> str:
    if correct:
        return "correct"
    if not raw_response.strip():
        return "empty_response"
    if prediction is None:
        return "no_choice_found"
    return "wrong_choice"


def _model_metadata(model_name: str, temperature: float, max_tokens: int, base_url: str | None) -> dict[str, Any]:
    provider, _, model_id = model_name.partition("/")
    model_id = model_id or model_name
    family = model_id.split("/")[-1].split("-")[0] if model_id else model_name

    return {
        "provider": provider if model_id != model_name else "unknown",
        "model_id": model_id,
        "model_family": family,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "base_url_configured": base_url is not None,
    }


def _ci_metadata() -> dict[str, Any]:
    keys = {
        "github_sha": "GITHUB_SHA",
        "github_ref": "GITHUB_REF_NAME",
        "github_run_id": "GITHUB_RUN_ID",
        "github_actor": "GITHUB_ACTOR",
        "gitlab_commit_sha": "CI_COMMIT_SHA",
        "gitlab_ref": "CI_COMMIT_REF_NAME",
        "gitlab_pipeline_id": "CI_PIPELINE_ID",
        "gitlab_job_id": "CI_JOB_ID",
    }
    return {name: os.environ[value] for name, value in keys.items() if os.environ.get(value)}


def _dataset_coverage(result_items: list[dict[str, Any]]) -> dict[str, Any]:
    fields = ["subject", "domain", "difficulty", "language_style", "source"]
    coverage: dict[str, Any] = {
        "total_items": len(result_items),
    }

    for field in fields:
        values = sorted({str(item.get(field) or "unknown") for item in result_items})
        coverage[field] = {
            "count": len(values),
            "values": values,
        }

    years = sorted(
        {
            str(item.get("metadata", {}).get("year"))
            for item in result_items
            if item.get("metadata", {}).get("year") is not None
        }
    )
    grades = sorted(
        {
            str(item.get("metadata", {}).get("grade"))
            for item in result_items
            if item.get("metadata", {}).get("grade") is not None
        }
    )
    coverage["years"] = years
    coverage["grades"] = grades
    return coverage


def _answer_distribution(result_items: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for item in result_items:
        prediction = item.get("prediction")
        counts[str(prediction) if prediction else "invalid"] += 1
    return {label: counts.get(label, 0) for label in (*ANSWER_LABELS, "invalid")}


def _confusion_matrix(result_items: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    labels = (*ANSWER_LABELS, "invalid")
    matrix = {gold: {prediction: 0 for prediction in labels} for gold in ANSWER_LABELS}
    for item in result_items:
        gold = str(item.get("gold") or "")
        prediction = str(item.get("prediction") or "invalid")
        if gold in matrix:
            matrix[gold][prediction if prediction in labels else "invalid"] += 1
    return matrix


def build_result_item(
    *,
    item: MCQItem,
    prediction: str | None,
    raw_response: str,
    correct: bool,
    prompt: str | None = None,
) -> dict[str, Any]:
    return {
        "id": item.id,
        "question": item.question,
        "choices": [{"label": label, "text": text} for label, text in item.labelled_choices],
        "gold": item.answer_label,
        "prediction": prediction,
        "raw_response": raw_response,
        "correct": correct,
        "failure_category": _failure_category(
            prediction=prediction,
            raw_response=raw_response,
            correct=correct,
        ),
        "prompt": prompt,
        "subject": item.subject,
        "domain": item.domain,
        "difficulty": item.difficulty,
        "language_style": item.language_style,
        "source": item.source,
        "metadata": item.metadata,
    }


def build_result_payload(
    *,
    engine: str,
    dataset_path: Path,
    model_name: str,
    prompt_name: str,
    result_items: list[dict[str, Any]],
    temperature: float = 0.0,
    max_tokens: int = 16,
    base_url: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    correct_count = sum(int(bool(item["correct"])) for item in result_items)
    invalid_count = sum(int(item["prediction"] is None) for item in result_items)
    failure_categories = dict(Counter(str(item.get("failure_category", "unknown")) for item in result_items))
    generated_at = datetime.now(UTC).isoformat()

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": generated_at,
        "generated_at": generated_at,
        "framework": "egeyuma",
        "engine": engine,
        "model": model_name,
        "model_metadata": _model_metadata(model_name, temperature, max_tokens, base_url),
        "task": "mcq",
        "dataset": str(dataset_path),
        "dataset_coverage": _dataset_coverage(result_items),
        "prompt_version": prompt_name,
        "prompt_template": load_prompt_template(prompt_name),
        "run_notes": os.environ.get("EGEYUMA_RUN_NOTES"),
        "ci": _ci_metadata(),
        "total": len(result_items),
        "correct": correct_count,
        "accuracy": _accuracy(correct_count, len(result_items)),
        "invalid_response_count": invalid_count,
        "invalid_response_rate": _accuracy(invalid_count, len(result_items)),
        "failure_categories": failure_categories,
        "answer_distribution": _answer_distribution(result_items),
        "confusion_matrix": _confusion_matrix(result_items),
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
    log: LogFn = null_log,
) -> dict[str, Any]:
    log(f"Loading dataset: {dataset_path}")
    dataset = load_mcq_jsonl(dataset_path)
    log(f"Loaded {len(dataset)} MCQ items")
    log(f"Creating model adapter: {model_name}")
    model = create_model_adapter(
        model_name,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    result_items: list[dict[str, Any]] = []
    started_at = monotonic()
    correct_count = 0
    invalid_count = 0

    for index, item in enumerate(dataset, start=1):
        item_started_at = monotonic()
        log(f"[{index}/{len(dataset)}] Generating response for {item.id}")
        prompt = render_mcq_prompt(item, prompt_name)
        response = model.generate(prompt)
        prediction = extract_choice(response.raw_response)
        correct = is_correct(prediction, item.answer_label)
        correct_count += int(correct)
        invalid_count += int(prediction is None)
        running_accuracy = _accuracy(correct_count, index) * 100
        log(
            f"[{index}/{len(dataset)}] gold={item.answer_label} "
            f"prediction={prediction or 'invalid'} correct={correct} "
            f"elapsed={monotonic() - item_started_at:.1f}s "
            f"accuracy={running_accuracy:.2f}% invalid={invalid_count}"
        )

        result_items.append(
            build_result_item(
                item=item,
                prediction=prediction,
                raw_response=response.raw_response,
                correct=correct,
                prompt=prompt,
            )
        )

    log(f"Completed generation in {monotonic() - started_at:.1f}s")
    payload = build_result_payload(
        engine="native",
        dataset_path=dataset_path,
        model_name=model_name,
        prompt_name=prompt_name,
        result_items=result_items,
        temperature=temperature,
        max_tokens=max_tokens,
        base_url=base_url,
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
    log: LogFn = null_log,
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
            log=log,
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
            log=log,
        )

    raise ValueError(f"Unsupported engine {engine!r}. Supported engines: native, inspect")
