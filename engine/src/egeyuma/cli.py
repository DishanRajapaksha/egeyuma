from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import typer
from rich.console import Console

from egeyuma.datasets.jsonl import DatasetValidationError, load_mcq_jsonl
from egeyuma.datasets.sinhalammlu import resolve_dataset_path
from egeyuma.reporting import load_result, render_text_report
from egeyuma.runner import run_mcq_evaluation

app = typer.Typer(help="Sinhala and Sri Lankan-context LLM evaluation tooling.")
console = Console()


@app.command()
def validate(
    dataset: Annotated[str, typer.Argument(help="Path or dataset alias such as sinhalammlu.")],
    refresh_dataset: Annotated[
        bool,
        typer.Option(help="Refresh cached remote datasets before validating."),
    ] = False,
    dataset_limit: Annotated[
        int | None,
        typer.Option(help="Maximum remote dataset records to materialize."),
    ] = None,
) -> None:
    """Validate a JSONL dataset against the canonical MCQ schema."""

    try:
        dataset_path = resolve_dataset_path(
            dataset,
            refresh=refresh_dataset,
            limit=dataset_limit,
        )
        items = load_mcq_jsonl(dataset_path)
    except DatasetValidationError as exc:
        console.print(f"[red]Invalid dataset:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Valid dataset[/green]: {dataset_path} ({len(items)} items)")


@app.command()
def run(
    dataset: Annotated[
        str,
        typer.Option(help="Path to canonical MCQ JSONL dataset, or sinhalammlu."),
    ],
    output: Annotated[Path, typer.Option(help="Output result JSON path.")],
    engine: Annotated[
        Literal["native", "inspect"],
        typer.Option(help="Evaluation engine: native or inspect."),
    ] = "native",
    model: Annotated[
        str,
        typer.Option(
            help=(
                "Model name. Supports constant/A ... constant/E, openai/<model>, "
                "mistral/<model>, lmstudio/<model>."
            ),
        ),
    ] = "constant/B",
    prompt: Annotated[
        str,
        typer.Option(help="Prompt template name."),
    ] = "mcq_si_subject_v1",
    base_url: Annotated[
        str | None,
        typer.Option(
            help="Override OpenAI-compatible API base URL, for example http://localhost:1234/v1."
        ),
    ] = None,
    api_key: Annotated[
        str | None,
        typer.Option(help="Override API key. Defaults to provider-specific environment variables."),
    ] = None,
    temperature: Annotated[
        float,
        typer.Option(help="Generation temperature for API-backed models."),
    ] = 0.0,
    max_tokens: Annotated[
        int,
        typer.Option(help="Maximum generated tokens for API-backed models."),
    ] = 16,
    refresh_dataset: Annotated[
        bool,
        typer.Option(help="Refresh cached remote datasets before running."),
    ] = False,
    dataset_limit: Annotated[
        int | None,
        typer.Option(help="Maximum remote dataset records to materialize."),
    ] = None,
) -> None:
    """Run an MCQ evaluation."""

    dataset_path = resolve_dataset_path(
        dataset,
        refresh=refresh_dataset,
        limit=dataset_limit,
    )
    result = run_mcq_evaluation(
        dataset_path=dataset_path,
        model_name=model,
        prompt_name=prompt,
        output_path=output,
        engine=engine,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    console.print(f"[green]Wrote[/green] {output}")
    console.print(f"Accuracy: {result['accuracy'] * 100:.2f}%")


@app.command()
def report(input: Path) -> None:
    """Print a text report for a result JSON file."""

    result = load_result(input)
    console.print(render_text_report(result))
