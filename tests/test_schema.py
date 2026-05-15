import pytest
from pydantic import ValidationError

from egeyuma.datasets.schema import MCQItem


def test_valid_mcq_item() -> None:
    item = MCQItem(
        id="x",
        question="ප්‍රශ්නය?",
        choices=["A", "B", "C", "D"],
        answer_index=1,
        answer_label="B",
    )

    assert item.answer_label == "B"
    assert item.labelled_choices[1] == ("B", "B")


def test_answer_index_and_label_must_align() -> None:
    with pytest.raises(ValidationError):
        MCQItem(
            id="x",
            question="ප්‍රශ්නය?",
            choices=["A", "B", "C", "D"],
            answer_index=1,
            answer_label="C",
        )
