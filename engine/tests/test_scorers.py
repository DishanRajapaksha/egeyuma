from __future__ import annotations

from egeyuma.scorers import extract_choice, is_correct


def test_extract_choice_accepts_clean_letters() -> None:
    assert extract_choice("A") == "A"
    assert extract_choice(" b ") == "B"


def test_extract_choice_extracts_first_standalone_letter() -> None:
    assert extract_choice("The answer is C.") == "C"
    assert extract_choice("පිළිතුර D වේ.") == "D"


def test_extract_choice_returns_none_for_missing_choice() -> None:
    assert extract_choice("I do not know") is None
    assert extract_choice("") is None


def test_is_correct() -> None:
    assert is_correct("A", "A") is True
    assert is_correct("A", "B") is False
    assert is_correct(None, "A") is False
