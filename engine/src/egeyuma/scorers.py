from __future__ import annotations

import re

from egeyuma.datasets.schema import ANSWER_LABELS

ANSWER_PATTERN = re.compile(r"\b([A-E])\b", re.IGNORECASE)


def extract_choice(raw_response: str) -> str | None:
    cleaned = raw_response.strip().upper()
    if cleaned in ANSWER_LABELS:
        return cleaned

    match = ANSWER_PATTERN.search(cleaned)
    if match:
        return match.group(1).upper()

    return None


def is_correct(prediction: str | None, gold: str) -> bool:
    return prediction == gold
