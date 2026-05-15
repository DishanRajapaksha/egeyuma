from __future__ import annotations

from pathlib import Path

from egeyuma.datasets.schema import MCQItem

PROMPT_DIR = Path(__file__).resolve().parent / "prompt_templates"


class PromptTemplateError(Exception):
    """Raised when a prompt template cannot be rendered."""


def load_prompt_template(prompt_name: str) -> str:
    path = PROMPT_DIR / f"{prompt_name}.txt"
    if not path.exists():
        available = ", ".join(sorted(p.stem for p in PROMPT_DIR.glob("*.txt")))
        raise PromptTemplateError(
            f"Unknown prompt template {prompt_name!r}. Available templates: {available}"
        )
    return path.read_text(encoding="utf-8")


def render_mcq_prompt(item: MCQItem, prompt_name: str) -> str:
    template = load_prompt_template(prompt_name)
    choices = dict(item.labelled_choices)

    values = {
        "id": item.id,
        "question": item.question,
        "subject": item.subject or "සාමාන්‍ය දැනුම",
        "domain": item.domain or "unknown",
        "difficulty": item.difficulty or "unknown",
        "choice_a": choices.get("A", ""),
        "choice_b": choices.get("B", ""),
        "choice_c": choices.get("C", ""),
        "choice_d": choices.get("D", ""),
        "choice_e": choices.get("E", ""),
        "choices": "\n".join(f"{label}. {choice}" for label, choice in item.labelled_choices),
    }

    try:
        return template.format(**values)
    except KeyError as exc:
        raise PromptTemplateError(f"Prompt template references unknown field: {exc}") from exc
