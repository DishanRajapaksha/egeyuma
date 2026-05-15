from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


ANSWER_LABELS = tuple("ABCDE")


class MCQItem(BaseModel):
    """Canonical SinhalaEval-style multiple-choice item.

    Keep this schema stable. Dataset converters should adapt external datasets into this
    shape before they enter the runner.
    """

    id: str
    task_type: Literal["mcq"] = "mcq"
    question: str = Field(min_length=1)
    choices: list[str] = Field(min_length=2, max_length=5)
    answer_index: int = Field(ge=0, le=4)
    answer_label: str
    subject: str | None = None
    domain: str | None = None
    difficulty: str | None = None
    language_style: str = "formal_sinhala"
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("answer_label")
    @classmethod
    def normalise_answer_label(cls, value: str) -> str:
        label = value.strip().upper()
        if label not in ANSWER_LABELS:
            raise ValueError(f"answer_label must be one of {ANSWER_LABELS}")
        return label

    @model_validator(mode="after")
    def validate_answer_alignment(self) -> MCQItem:
        expected_label = ANSWER_LABELS[self.answer_index]
        if self.answer_label != expected_label:
            raise ValueError(
                f"answer_label {self.answer_label!r} does not match "
                f"answer_index {self.answer_index}; expected {expected_label!r}"
            )
        if self.answer_index >= len(self.choices):
            raise ValueError("answer_index points outside choices")
        return self

    @property
    def labelled_choices(self) -> list[tuple[str, str]]:
        return [(ANSWER_LABELS[index], choice) for index, choice in enumerate(self.choices)]
