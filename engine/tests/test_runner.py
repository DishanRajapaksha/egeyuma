from __future__ import annotations

import json
from pathlib import Path

from egeyuma.runner import run_mcq_evaluation


DATASET_ITEMS: list[dict[str, object]] = [
    {
        "id": "item_a",
        "question": "A නිවැරදි පිළිතුර වන ප්‍රශ්නයකි.",
        "choices": ["one", "two", "three", "four"],
        "answer_index": 0,
        "answer_label": "A",
        "subject": "Smoke",
        "domain": "Test",
        "difficulty": "easy",
    },
    {
        "id": "item_b",
        "question": "B නිවැරදි පිළිතුර වන ප්‍රශ්නයකි.",
        "choices": ["one", "two", "three", "four"],
        "answer_index": 1,
        "answer_label": "B",
        "subject": "Smoke",
        "domain": "Test",
        "difficulty": "easy",
    },
]


def _write_dataset(path: Path) -> None:
    path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in DATASET_ITEMS),
        encoding="utf-8",
    )


def test_run_native_mcq_evaluation_writes_result_file(tmp_path: Path) -> None:
    dataset_path = tmp_path / "dataset.jsonl"
    output_path = tmp_path / "result.json"
    _write_dataset(dataset_path)

    result = run_mcq_evaluation(
        dataset_path=dataset_path,
        model_name="constant/B",
        prompt_name="mcq_si_subject_v1",
        output_path=output_path,
        engine="native",
    )

    assert output_path.exists()
    assert result["total"] == 2
    assert result["correct"] == 1
    assert result["accuracy"] == 0.5
    assert result["invalid_response_count"] == 0
    assert result["items"][0]["prediction"] == "B"
    assert result["items"][0]["correct"] is False
    assert result["items"][1]["prediction"] == "B"
    assert result["items"][1]["correct"] is True

    persisted = json.loads(output_path.read_text(encoding="utf-8"))
    assert persisted["framework"] == "egeyuma"
    assert persisted["engine"] == "native"


def test_run_native_mcq_evaluation_calculates_breakdowns(tmp_path: Path) -> None:
    dataset_path = tmp_path / "dataset.jsonl"
    output_path = tmp_path / "result.json"
    _write_dataset(dataset_path)

    result = run_mcq_evaluation(
        dataset_path=dataset_path,
        model_name="constant/B",
        prompt_name="mcq_si_subject_v1",
        output_path=output_path,
        engine="native",
    )

    assert result["breakdowns"]["subject"] == {"Smoke": 0.5}
    assert result["breakdowns"]["domain"] == {"Test": 0.5}
    assert result["breakdowns"]["difficulty"] == {"easy": 0.5}
