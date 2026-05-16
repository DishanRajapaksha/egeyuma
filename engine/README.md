# Egeyuma Engine

Python evaluation engine for Sinhala, Singlish, and Sri Lankan-context LLM benchmarks.

## Install

```bash
cd engine
uv sync --all-extras --dev
```

## Validate a dataset

```bash
uv run egeyuma validate ../data/samples/sinhalammlu_sample.jsonl
```

## Run a smoke-test evaluation

```bash
uv run egeyuma run \
  --dataset ../data/samples/sinhalammlu_sample.jsonl \
  --model constant/B \
  --prompt mcq_si_subject_v1 \
  --output ../results/sample-run.json
```

## Run through Inspect AI

```bash
uv run egeyuma run \
  --engine inspect \
  --dataset ../data/samples/sinhalammlu_sample.jsonl \
  --model openai/gpt-4o-mini \
  --prompt mcq_si_subject_v1 \
  --output ../results/inspect-openai-run.json
```

For real models, the Inspect engine uses Inspect AI's native model-provider abstraction via its `generate()` solver. The `constant/A` ... `constant/E` models are the only exception: they use a tiny custom solver so smoke tests can run offline.

Inspect logs are written next to the result file under `inspect-logs/`.

## Generate a report

```bash
uv run egeyuma report ../results/sample-run.json
```

## Development

```bash
uv run ruff check .
uv run mypy src tests
uv run pytest
```
