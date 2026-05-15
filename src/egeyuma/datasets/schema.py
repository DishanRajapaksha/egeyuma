from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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


class SinhalaMMLURawItem(BaseModel):
    """Raw SinhalaMMLU record shape.

    The dataset uses 1-based numeric answers. SinhalaEval converts that into the
    canonical zero-based index plus A/B/C/D/E label before running evaluations.
    """

    model_config = ConfigDict(extra="allow")

    q_no: int
    subject: str
    category: str
    question: str = Field(min_length=1)
    choices: list[str] = Field(min_length=2, max_length=5)
    answer: int = Field(ge=1, le=5)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_answer_range(self) -> SinhalaMMLURawItem:
        if self.answer > len(self.choices):
            raise ValueError("answer points outside choices")
        return self

    def to_mcq_item(self) -> MCQItem:
        answer_index = self.answer - 1
        source = self.metadata.get("source")
        difficulty = self.metadata.get("difficulty")
        grade = self.metadata.get("grade")
        year = self.metadata.get("year")
        paper_type = self.metadata.get("type")

        # q_no is only local to a paper/subject. Keep a readable prefix, then add a
        # content/source hash so merged SinhalaMMLU files cannot silently collide.
        stable_id_parts = [
            "sinhalammlu",
            self.category,
            self.subject,
            f"grade_{grade}" if grade is not None else None,
            f"year_{year}" if year is not None else None,
            paper_type,
            f"q_{self.q_no}",
        ]
        stable_id_prefix = "_".join(
            _slugify(part) for part in stable_id_parts if part is not None and str(part).strip()
        )
        stable_id = f"{stable_id_prefix}_{_short_raw_hash(self)}"

        return MCQItem(
            id=stable_id,
            question=self.question,
            choices=self.choices,
            answer_index=answer_index,
            answer_label=ANSWER_LABELS[answer_index],
            subject=self.subject,
            domain=self.category,
            difficulty=str(difficulty) if difficulty is not None else None,
            language_style="formal_sinhala",
            source=str(source) if source is not None else "SinhalaMMLU",
            metadata={
                **self.metadata,
                "q_no": self.q_no,
                "subject_original": self.metadata.get("subject_original"),
                "raw_category": self.category,
            },
        )


def coerce_mcq_item(raw: dict[str, Any]) -> MCQItem:
    """Accept either canonical SinhalaEval MCQ JSON or raw SinhalaMMLU JSON."""

    if "answer_index" in raw and "answer_label" in raw and "id" in raw:
        return MCQItem.model_validate(raw)

    if {"q_no", "category", "answer"}.issubset(raw):
        return SinhalaMMLURawItem.model_validate(raw).to_mcq_item()

    return MCQItem.model_validate(raw)


def _short_raw_hash(item: SinhalaMMLURawItem) -> str:
    payload = {
        "q_no": item.q_no,
        "subject": item.subject,
        "category": item.category,
        "question": item.question,
        "choices": item.choices,
        "answer": item.answer,
        "source": item.metadata.get("source"),
        "year": item.metadata.get("year"),
        "type": item.metadata.get("type"),
        "grade": item.metadata.get("grade"),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha1(encoded).hexdigest()[:10]


def _slugify(value: object) -> str:
    text = str(value).strip().lower()
    safe = []
    for char in text:
        if char.isalnum():
            safe.append(char)
        elif char in {" ", "-", "_", "/"}:
            safe.append("_")
    return "".join(safe).strip("_") or "unknown"
