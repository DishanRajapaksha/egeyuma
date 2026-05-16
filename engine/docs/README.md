# Egeyuma Engine

The engine is the Python package and CLI under `engine/`. It owns dataset loading,
prompt rendering, model execution, scoring, Inspect AI integration, and result JSON
generation.

## Layout

```text
engine/
  pyproject.toml
  src/egeyuma/
    cli.py
    runner.py
    inspect_runner.py
    models.py
    scorers.py
    reporting.py
    datasets/
    prompt_templates/
  tests/
```

## Dataset Flow

Input datasets enter the runner as canonical MCQ JSONL. The loader accepts either
canonical records or raw SinhalaMMLU records and converts them into the stable
`MCQItem` schema before prompts are rendered.

The `sinhalammlu` dataset alias resolves the restricted Hugging Face dataset
`naist-nlp/SinhalaMMLU`. The first materialization writes a converted local cache
under `engine/.cache/egeyuma/sinhalammlu.jsonl`. Set `HF_TOKEN` in the shell or
`engine/.env` before using the alias.

## Sinhala Text Normalisation

Future Sinhala evaluation work may benefit from a dedicated text normalisation step
before scoring. The most relevant upstream project found so far is
[`google-research/nisaba`](https://github.com/google-research/nisaba), a Google
Research library for script processing based on finite-state transducers.

Nisaba is useful plumbing for Unicode and script hygiene, especially for Sinhala and
other Indic scripts. It may help with:

- NFC and visual normalisation before exact-match or label extraction.
- Detecting malformed Sinhala character sequences in datasets or model outputs.
- Making answer parsing less brittle when equivalent-looking text uses different
  Unicode sequences.
- Future transliteration or script-validation experiments.

It should not be treated as a semantic grader, model evaluator, dashboard, or Inspect
AI replacement. If added, keep it as an optional preprocessing layer in the dataset
or response-normalisation path, then measure whether it improves invalid-response
rates and exact-match stability.

## Model Providers

The native runner supports:

- `constant/A` through `constant/E` for deterministic smoke tests.
- `openai/<model>` for OpenAI-compatible Chat Completions.
- `mistral/<model>` for Mistral's OpenAI-compatible endpoint.
- `lmstudio/<model>` for LM Studio's OpenAI-compatible endpoint.

LM Studio reasoning models can spend many tokens in reasoning before producing final
message content. Use a larger `--max-tokens` value, such as `2048`, for local
reasoning models.

## Inspect AI

The Inspect engine uses Inspect AI's native provider abstraction for real models.
The constant models still use a custom deterministic solver so offline smoke tests
remain stable. Inspect logs are written next to the output JSON under
`inspect-logs/`.

## Result Contract

Result JSON files include:

- run metadata: model, engine, dataset, prompt version, run id
- aggregate metrics: total, correct, accuracy, invalid response count/rate
- breakdowns: subject, domain, difficulty, language style
- item-level records: id, gold label, prediction, raw response, correctness, metadata

The dashboard reads these JSON files directly from the repository-level `results/`
directory.

## Development Notes

Keep engine changes scoped to the Python package unless the result contract changes.
When the result contract changes, update dashboard loading and rendering at the same
time.

Run tests from `engine/` so `pyproject.toml` and the package path resolve correctly.

