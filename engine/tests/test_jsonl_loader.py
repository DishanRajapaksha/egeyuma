from __future__ import annotations

import json

import pytest

from egeyuma.datasets.jsonl import DatasetValidationError, load_mcq_jsonl, write_json


RAW_ITEM = {
    "q_no": 1,
    "subject": "Science",
    "category": "stem",
    "question": "ජලයේ රසායනික සූත්‍රය කුමක්ද?",
    "choices": ["CO2", "H2O", "O2", "NaCl"],
    "answer": 2,
    "metadata": {"difficulty": "easy", "grade": 6, "source": "manual_sample"},
}

CANONICAL_ITEM = {
    "id": "canonical_science_001",
    "question": "ජලයේ රසායනික සූත්‍රය කුමක්ද?",
    "choices": ["CO2", "H2O", "O2", "NaCl"],
    "answer_index": 1,
    "answer_label": "B",
    "subject": "Science",
    "domain": "STEM",
}


def test_load_mcq_jsonl_accepts_raw_and_canonical_records(tmp_path) -> None:
    dataset_path = tmp_path / "dataset.jsonl"
    dataset_path.write_text(
        "\n".join(
            [
                json.dumps(RAW_ITEM, ensure_ascii=False),
                json.dumps(CANONICAL_ITEM, ensure_ascii=False),
            ]
        ),
        encoding="utf-8",
    )

    items = load_mcq_jsonl(dataset_path)

    assert len(items) == 2
    assert items[0].answer_label == "B"
    assert items[0].domain == "stem"
    assert items[1].id == "canonical_science_001"
    assert items[1].answer_label == "B"


def test_load_mcq_jsonl_skips_blank_lines(tmp_path) -> None:
    dataset_path = tmp_path / "dataset.jsonl"
    dataset_path.write_text(
        f"\n{json.dumps(CANONICAL_ITEM, ensure_ascii=False)}\n\n",
        encoding="utf-8",
    )

    items = load_mcq_jsonl(dataset_path)

    assert len(items) == 1
    assert items[0].id == "canonical_science_001"


def test_load_mcq_jsonl_reports_invalid_json_with_line_number(tmp_path) -> None:
    dataset_path = tmp_path / "bad.jsonl"
    dataset_path.write_text("{not-json}\n", encoding="utf-8")

    with pytest.raises(DatasetValidationError, match="bad.jsonl:1: invalid JSON"):
        load_mcq_jsonl(dataset_path)


def test_load_mcq_jsonl_reports_validation_error_with_line_number(tmp_path) -> None:
    dataset_path = tmp_path / "bad-schema.jsonl"
    bad_item = {**CANONICAL_ITEM, "answer_index": 3, "answer_label": "B"}
    dataset_path.write_text(json.dumps(bad_item, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(DatasetValidationError, match="bad-schema.jsonl:1"):
        load_mcq_jsonl(dataset_path)


def test_write_json_creates_parent_directory(tmp_path) -> None:
    output_path = tmp_path / "nested" / "result.json"

    write_json(output_path, {"සිංහල": "ok"})

    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == {"සිංහල": "ok"}
