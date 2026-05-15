from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from egeyuma.datasets.jsonl import DatasetValidationError, load_mcq_jsonl
from egeyuma.reporting import load_result, render_text_report
from egeyuma.runner import run_mcq_evaluation

app = typer.Typer(help="Sinhala and Sri Lankan-context LLM evaluation tooling.")
console = Console()


@app.command()
def validate(dataset: Path) -> None:
    """Validate a JSONL dataset against the canonical MCQ schema."""

    try:
        items = load_mcq_jsonl(dataset)
    except DatasetValidationError as exc:
        console.print(f"[red]Invalid dataset:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Valid dataset[/green]: {dataset} ({len(items)} items)")


@app.command()
def run(
    dataset: Path = typer.Option(..., help="Path to canonical MCQ JSONL dataset."),
    model: str = typer.Option("constant/B", help="Model name. Scaffold supports constant/A ... constant/E."),
    prompt: str = typer.Option("mcq_si_subject_v1", help="Prompt template name."),
    output: Path = typer.Option(..., help="Output result JSON path."),
) -> None:
    """Run an MCQ evaluation."""

    result = run_mcq_evaluation(
        dataset_path=dataset,
        model_name=model,
        prompt_name=prompt,
        output_path=output,
    )
    console.print(f"[green]Wrote[/green] {output}")
    console.print(f"Accuracy: {result['accuracy'] * 100:.2f}%")


@app.command()
def report(input: Path) -> None:
    """Print a text report for a result JSON file."""

    result = load_result(input)
    console.print(render_text_report(result))
