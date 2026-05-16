# Egeyuma

Evaluation tooling for Sinhala, Singlish, and Sri Lankan-context LLMs.

Egeyuma is split into two workspaces:

```text
egeyuma/
  engine/       # Python evaluation engine and CLI
  dashboard/    # SvelteKit dashboard for visualising results
  data/         # sample datasets and fixtures
  results/      # local evaluation outputs, gitignored
```

## Engine

The Python engine owns dataset loading, prompt rendering, model execution, scoring, Inspect AI integration, and result JSON generation.

```bash
cd engine
uv sync --all-extras --dev
uv run egeyuma validate ../data/samples/sinhalammlu_sample.jsonl
```

Run a deterministic smoke test:

```bash
uv run egeyuma run \
  --dataset ../data/samples/sinhalammlu_sample.jsonl \
  --model constant/B \
  --prompt mcq_si_subject_v1 \
  --output ../results/sample-run.json
```

Run through Inspect AI:

```bash
uv run egeyuma run \
  --engine inspect \
  --dataset ../data/samples/sinhalammlu_sample.jsonl \
  --model openai/gpt-4o-mini \
  --prompt mcq_si_subject_v1 \
  --output ../results/inspect-openai-run.json
```

For real models, the Inspect engine uses Inspect AI's native model-provider abstraction via its `generate()` solver. The `constant/A` ... `constant/E` models are the only exception: they use a tiny custom solver so smoke tests can run offline.

Generate a report:

```bash
uv run egeyuma report ../results/sample-run.json
```

## Dashboard

The SvelteKit dashboard is the future visual layer for result JSON files and leaderboard-style comparisons.

```bash
cd dashboard
npm install
npm run dev
```

Current dashboard scope:

- landing page scaffold
- future result JSON import
- future accuracy breakdowns by subject, domain, difficulty, and language style
- future links to Inspect logs for sample-level debugging

## Development

Engine checks:

```bash
cd engine
uv run ruff check .
uv run mypy src tests
uv run pytest
```

Dashboard checks:

```bash
cd dashboard
npm run check
npm run build
```

## Design principles

- Egeyuma owns the dataset schema, prompt versions, result schema, and reports.
- Inspect AI is used as an execution engine, but the data and result contracts stay framework-neutral.
- The dashboard reads result artifacts; it should not own evaluation logic.
- JSONL in, JSON out. Boring pipes, sharp knives.
