from pathlib import Path

import pytest

from egeyuma.runner import run_mcq_evaluation

SAMPLE_DATASET = Path("data/samples/sinhalammlu_sample.jsonl")


def test_native_engine_writes_result(tmp_path: Path) -> None:
    output_path = tmp_path / "native.json"

    result = run_mcq_evaluation(
        dataset_path=SAMPLE_DATASET,
        model_name="constant/B",
        prompt_name="mcq_si_subject_v1",
        output_path=output_path,
    )

    assert output_path.exists()
    assert result["engine"] == "native"
    assert result["accuracy"] == 0.5


def test_inspect_engine_writes_result(tmp_path: Path) -> None:
    output_path = tmp_path / "inspect.json"

    result = run_mcq_evaluation(
        dataset_path=SAMPLE_DATASET,
        model_name="constant/B",
        prompt_name="mcq_si_subject_v1",
        output_path=output_path,
        engine="inspect",
    )

    assert output_path.exists()
    assert result["engine"] == "inspect"
    assert result["accuracy"] == 0.5
    assert result["metadata"]["inspect_log_dir"] == str(tmp_path / "inspect-logs")


def test_rejects_unknown_engine(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unsupported engine"):
        run_mcq_evaluation(
            dataset_path=SAMPLE_DATASET,
            model_name="constant/B",
            prompt_name="mcq_si_subject_v1",
            output_path=tmp_path / "bad.json",
            engine="bad",  # type: ignore[arg-type]
        )
