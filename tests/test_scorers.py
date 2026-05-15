from egeyuma.scorers import extract_choice


def test_extract_plain_choice() -> None:
    assert extract_choice("B") == "B"


def test_extract_choice_from_sentence() -> None:
    assert extract_choice("The answer is C.") == "C"


def test_extract_invalid_choice() -> None:
    assert extract_choice("මම නොදනිමි") is None
