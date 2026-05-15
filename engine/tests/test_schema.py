from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from egeyuma.datasets.schema import MCQItem, SinhalaMMLURawItem, coerce_mcq_item


RAW_SINHALAMMLU_ITEM: dict[str, Any] = {
    "q_no": 1,
    "subject": "Arts",
    "category": "humanities",
    "question": "වෙසක් උත්සවයේදී බෞද්ධයින් අනුගමනය කරන පූජා විධි දෙක නම්,",
    "choices": [
        "ආමිස පූජා සහ ප්‍රතිපත්ති පූජා",
        "මල් පූජා හා පහන් පූජා",
        "ද්‍රව්‍ය පූජා සහ භාණ්ඩ පූජා",
        "ආහාර පූජා හා වස්ත්‍ර පූජා",
    ],
    "answer": 1,
    "metadata": {
        "subject_original": "චිත්‍ර",
        "difficulty": "easy",
        "grade": 6,
        "type": "P_NWP_3",
        "year": 2022,
        "source": "https://pastpapers.wiki/example",
    },
}


def test_raw_sinhalammlu_item_converts_to_canonical_mcq() -> None:
    item = SinhalaMMLURawItem.model_validate(RAW_SINHALAMMLU_ITEM).to_mcq_item()

    assert item.answer_index == 0
    assert item.answer_label == "A"
    assert item.subject == "Arts"
    assert item.domain == "humanities"
    assert item.difficulty == "easy"
    assert item.source == "https://pastpapers.wiki/example"
    assert item.metadata["q_no"] == 1
    assert item.metadata["subject_original"] == "චිත්‍ර"
    assert item.id.startswith("sinhalammlu_humanities_arts_grade_6_year_2022_p_nwp_3_q_1_")
    assert len(item.id.rsplit("_", maxsplit=1)[1]) == 10


def test_raw_sinhalammlu_id_is_stable() -> None:
    first = SinhalaMMLURawItem.model_validate(RAW_SINHALAMMLU_ITEM).to_mcq_item()
    second = SinhalaMMLURawItem.model_validate(RAW_SINHALAMMLU_ITEM).to_mcq_item()

    assert first.id == second.id


def test_raw_sinhalammlu_id_changes_when_source_changes() -> None:
    first = SinhalaMMLURawItem.model_validate(RAW_SINHALAMMLU_ITEM).to_mcq_item()
    metadata = dict(RAW_SINHALAMMLU_ITEM["metadata"])
    modified = {
        **RAW_SINHALAMMLU_ITEM,
        "metadata": {**metadata, "source": "https://other.example/paper"},
    }
    second = SinhalaMMLURawItem.model_validate(modified).to_mcq_item()

    assert first.id != second.id


def test_raw_sinhalammlu_rejects_answer_outside_choices() -> None:
    raw = {**RAW_SINHALAMMLU_ITEM, "answer": 5}

    with pytest.raises(ValidationError, match="answer does not match any choice"):
        SinhalaMMLURawItem.model_validate(raw)


def test_sinhalammlu_numeric_answer_can_be_choice_value() -> None:
    item = SinhalaMMLURawItem(
        q_no=1,
        subject="Civics",
        category="social_science",
        question="ප්‍රශ්නය?",
        choices=["04", "15", "24", "360"],
        answer=24,
    ).to_mcq_item()

    assert item.answer_index == 2
    assert item.answer_label == "C"


def test_canonical_mcq_rejects_mismatched_answer_label() -> None:
    with pytest.raises(ValidationError, match="answer_label 'A' does not match answer_index 1"):
        MCQItem.model_validate(
            {
                "id": "bad_item",
                "question": "question",
                "choices": ["one", "two"],
                "answer_index": 1,
                "answer_label": "A",
            }
        )


def test_coerce_accepts_raw_sinhalammlu_shape() -> None:
    item = coerce_mcq_item(RAW_SINHALAMMLU_ITEM)

    assert item.id.startswith("sinhalammlu_")
    assert item.answer_label == "A"


def test_coerce_accepts_canonical_shape() -> None:
    item = coerce_mcq_item(
        {
            "id": "canonical_001",
            "question": "question",
            "choices": ["one", "two"],
            "answer_index": 1,
            "answer_label": "B",
        }
    )

    assert item.id == "canonical_001"
    assert item.answer_label == "B"
