from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from inspect_ai import Task, eval
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import ModelOutput
from inspect_ai.scorer import CORRECT, INCORRECT, NOANSWER, Score, Scorer, Target, accuracy, scorer
from inspect_ai.solver import Generate, Solver, TaskState, solver

from egeyuma.datasets.jsonl import load_mcq_jsonl, write_json
from egeyuma.datasets.schema import MCQItem
from egeyuma.models import create_model_adapter
from egeyuma.prompts import render_mcq_prompt
from egeyuma.runner import build_result_item, build_result_payload
from egeyuma.scorers import extract_choice, is_correct


def build_egeyuma_model_solver(
    *,
    model_name: str,
    base_url: str | None,
    api_key: str | None,
    temperature: float,
    max_tokens: int,
) -> Solver:
    @solver("egeyuma_model_solver")
    def egeyuma_model_solver(
        *,
        model_name: str,
        base_url: str | None,
        temperature: float,
        max_tokens: int,
    ) -> Solver:
        adapter = create_model_adapter(
            model_name,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        async def solve(state: TaskState, generate: Generate) -> TaskState:
            response = adapter.generate(state.input_text)
            state.output = ModelOutput.from_content(
                model=f"{response.provider}/{response.model}",
                content=response.raw_response,
            )
            return state

        return solve

    return egeyuma_model_solver(
        model_name=model_name,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )


@scorer(metrics=[accuracy()])
def egeyuma_choice_scorer() -> Scorer:
    async def score(state: TaskState, target: Target) -> Score:
        prediction = extract_choice(state.output.completion)
        correct = is_correct(prediction, target.text)
        if prediction is None:
            value = NOANSWER
        else:
            value = CORRECT if correct else INCORRECT
        return Score(
            value=value,
            answer=prediction,
            metadata={"raw_response": state.output.completion},
        )

    return score


def _sample_from_item(item: MCQItem, prompt_name: str) -> Sample:
    return Sample(
        id=item.id,
        input=render_mcq_prompt(item, prompt_name),
        target=item.answer_label,
        metadata={
            "subject": item.subject,
            "domain": item.domain,
            "difficulty": item.difficulty,
            "language_style": item.language_style,
            "source": item.source,
            "answer_label": item.answer_label,
        },
    )


def _item_by_id(dataset: list[MCQItem]) -> dict[str, MCQItem]:
    return {item.id: item for item in dataset}


def _result_items_from_log_samples(
    samples: list[Any],
    dataset: list[MCQItem],
) -> list[dict[str, Any]]:
    by_id = _item_by_id(dataset)
    result_items: list[dict[str, Any]] = []

    for sample in samples:
        item = by_id[str(sample.id)]
        raw_response = str(sample.output.completion)
        prediction = extract_choice(raw_response)
        correct = is_correct(prediction, item.answer_label)
        result_items.append(
            build_result_item(
                item=item,
                prediction=prediction,
                raw_response=raw_response,
                correct=correct,
            )
        )

    return result_items


def run_inspect_mcq_evaluation(
    *,
    dataset_path: Path,
    model_name: str,
    prompt_name: str,
    output_path: Path,
    base_url: str | None = None,
    api_key: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 16,
) -> dict[str, Any]:
    dataset = load_mcq_jsonl(dataset_path)
    samples = [_sample_from_item(item, prompt_name) for item in dataset]
    inspect_log_dir = output_path.parent / "inspect-logs"

    task = Task(
        dataset=MemoryDataset(samples, name=dataset_path.stem, location=str(dataset_path)),
        solver=build_egeyuma_model_solver(
            model_name=model_name,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        ),
        scorer=egeyuma_choice_scorer(),
        name="egeyuma_mcq",
    )

    logs = eval(
        task,
        model="mockllm/model",
        display="none",
        log_dir=str(inspect_log_dir),
        log_format="json",
    )
    inspect_log = logs[0]
    if inspect_log.status != "success":
        raise RuntimeError(f"Inspect evaluation failed with status: {inspect_log.status}")

    result_items = _result_items_from_log_samples(
        cast(list[Any], inspect_log.samples or []),
        dataset,
    )
    payload = build_result_payload(
        engine="inspect",
        dataset_path=dataset_path,
        model_name=model_name,
        prompt_name=prompt_name,
        result_items=result_items,
        metadata={"inspect_log_dir": str(inspect_log_dir)},
    )
    write_json(output_path, payload)
    return payload
