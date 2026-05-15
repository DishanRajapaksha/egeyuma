from pathlib import Path
from typing import Any

import pytest

from egeyuma.datasets.jsonl import DatasetValidationError, load_mcq_jsonl
from egeyuma.datasets.sinhalammlu import (
    _hf_token,
    is_sinhalammlu_ref,
    materialize_sinhalammlu_dataset,
    resolve_dataset_path,
)


def test_recognises_sinhalammlu_aliases() -> None:
    assert is_sinhalammlu_ref("sinhalammlu")
    assert is_sinhalammlu_ref("sinhala-mmlu")
    assert is_sinhalammlu_ref("hf://naist-nlp/SinhalaMMLU")
    assert is_sinhalammlu_ref("naist-nlp/SinhalaMMLU")
    assert is_sinhalammlu_ref("https://huggingface.co/datasets/naist-nlp/SinhalaMMLU")
    assert is_sinhalammlu_ref(
        "https://huggingface.co/datasets/naist-nlp/SinhalaMMLU/commits/main"
    )


def test_resolve_dataset_path_keeps_local_path(tmp_path: Path) -> None:
    dataset = tmp_path / "data.jsonl"
    dataset.write_text("", encoding="utf-8")

    assert resolve_dataset_path(str(dataset)) == dataset


def test_materialize_sinhalammlu_dataset_from_hf_json(tmp_path: Path) -> None:
    def fake_fetch_json(url: str, token: str | None) -> Any:
        assert token == "token"
        if "tree/main" in url:
            return [
                {"type": "file", "path": "README.md"},
                {"type": "file", "path": "TEST/easy/Arts_humanities_easy_f_97.json"},
            ]
        return [
            {
                "q_no": 1,
                "subject": "Arts",
                "category": "humanities",
                "question": "ප්‍රශ්නය?",
                "choices": ["A", "B", "C", "D"],
                "answer": 2,
                "metadata": {"difficulty": "easy", "grade": 6},
            }
        ]

    output_path = tmp_path / "sinhalammlu.jsonl"
    count = materialize_sinhalammlu_dataset(
        output_path,
        token="token",
        fetch_json=fake_fetch_json,
    )

    assert count == 1
    items = load_mcq_jsonl(output_path)
    assert items[0].answer_label == "B"
    assert items[0].metadata["hf_dataset"] == "naist-nlp/SinhalaMMLU"
    assert items[0].metadata["hf_source_file"] == "TEST/easy/Arts_humanities_easy_f_97.json"


def test_resolve_sinhalammlu_requires_hf_token(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(DatasetValidationError, match="Set HF_TOKEN"):
        resolve_dataset_path("sinhalammlu", cache_path=Path("does-not-exist.jsonl"))


def test_hf_token_loads_project_env_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HF_TOKEN", raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text("OTHER=value\nHF_TOKEN='file-token'\n", encoding="utf-8")

    assert _hf_token(env_path) == "file-token"


def test_hf_token_prefers_process_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HF_TOKEN", "process-token")
    env_path = tmp_path / ".env"
    env_path.write_text("HF_TOKEN=file-token\n", encoding="utf-8")

    assert _hf_token(env_path) == "process-token"
