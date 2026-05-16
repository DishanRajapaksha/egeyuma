# Egeyuma

Evaluation tooling for Sinhala, Singlish, and Sri Lankan-context LLMs.

This repository is the starting point for a long-term SinhalaEval-style framework. The first target is multiple-choice evaluation for SinhalaMMLU-style datasets, with room to grow into Singlish, RAG, hallucination, and cultural-knowledge evaluation.

## Install

```bash
uv sync --all-extras --dev
```

## Validate a dataset

```bash
uv run egeyuma validate data/samples/sinhalammlu_sample.jsonl
```

## Run a smoke-test evaluation

The scaffold ships with a deterministic `constant` model provider so the pipeline can be tested without API keys.

```bash
uv run egeyuma run \
  --dataset data/samples/sinhalammlu_sample.jsonl \
  --model constant/B \
  --prompt mcq_si_subject_v1 \
  --output results/sample-run.json
```

Use `--engine inspect` to run through Inspect AI while still writing Egeyuma's result JSON:

```bash
uv run egeyuma run \
  --engine inspect \
  --dataset data/samples/sinhalammlu_sample.jsonl \
  --model openai/gpt-4o-mini \
  --prompt mcq_si_subject_v1 \
  --output results/inspect-openai-run.json
```

For real models, the Inspect engine uses Inspect AI's native model-provider abstraction via its `generate()` solver. The `constant/A` ... `constant/E` models are the only exception: they use a tiny custom solver so smoke tests can run offline.

Inspect logs are written next to the result file under `inspect-logs/`.

## Run an OpenAI-compatible model

Install the optional OpenAI SDK dependency if you did not use `--all-extras`:

```bash
uv sync --extra openai
```

OpenAI-compatible providers use the Chat Completions API in the native engine. The model name prefix selects defaults:

- `openai/<model>` uses `OPENAI_API_KEY` and optional `OPENAI_BASE_URL`
- `mistral/<model>` uses `MISTRAL_API_KEY` and `https://api.mistral.ai/v1`
- `lmstudio/<model>` uses `http://localhost:1234/v1` and a placeholder local key

Mistral example:

```bash
export MISTRAL_API_KEY=...
uv run egeyuma run \
  --dataset data/samples/sinhalammlu_sample.jsonl \
  --model mistral/mistral-small-latest \
  --prompt mcq_si_subject_v1 \
  --output results/mistral-run.json
```

LM Studio local server example:

```bash
uv run egeyuma run \
  --dataset data/samples/sinhalammlu_sample.jsonl \
  --model lmstudio/local-model \
  --prompt mcq_si_subject_v1 \
  --output results/lmstudio-run.json
```

Use `--base-url` and `--api-key` for any other OpenAI-compatible endpoint:

```bash
uv run egeyuma run \
  --dataset data/samples/sinhalammlu_sample.jsonl \
  --model openai/my-model \
  --base-url http://localhost:1234/v1 \
  --api-key local-key \
  --output results/openai-compatible-run.json
```

## Generate a report

```bash
uv run egeyuma report results/sample-run.json
```

## Development

Use `uv` for dependency and environment management:

```bash
uv sync --all-extras --dev
uv run ruff check .
uv run mypy src tests
uv run pytest
```

## Design principles

- Egeyuma owns the dataset schema, prompt versions, result schema, and reports.
- Inspect AI is used as an execution engine, but the data and result contracts stay framework-neutral.
- JSONL in, JSON out. Boring pipes, sharp knives.

## Current scope

Implemented scaffold:

- MCQ dataset schema
- JSONL loader and validator
- raw SinhalaMMLU schema conversion with collision-resistant IDs
- prompt template loading
- exact-choice scorer
- deterministic constant model adapter for smoke tests
- OpenAI-compatible model adapter for OpenAI, Mistral, and LM Studio-style APIs in the native engine
- Inspect AI execution engine using native Inspect providers for real models
- result writer
- basic report command

Next useful steps:

- add a SinhalaMMLU Hugging Face converter
- add per-subject/per-domain comparison reports
