# Egeyuma

Evaluation tooling for Sinhala, Singlish, and Sri Lankan-context LLMs.

This repository is the starting point for a long-term SinhalaEval-style framework. The first target is multiple-choice evaluation for SinhalaMMLU-style datasets, with room to grow into Singlish, RAG, hallucination, and cultural-knowledge evaluation.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Validate a dataset

```bash
sinhalaeval validate data/samples/sinhalammlu_sample.jsonl
```

## Run a smoke-test evaluation

The scaffold ships with a deterministic `constant` model provider so the pipeline can be tested without API keys.

```bash
sinhalaeval run \
  --dataset data/samples/sinhalammlu_sample.jsonl \
  --model constant/B \
  --prompt mcq_si_subject_v1 \
  --output results/sample-run.json
```

## Generate a report

```bash
sinhalaeval report results/sample-run.json
```

## Design principles

- SinhalaEval owns the dataset schema, prompt versions, result schema, and reports.
- Inspect AI can be used as an execution engine, but the data and result contracts stay framework-neutral.
- JSONL in, JSON out. Boring pipes, sharp knives.

## Current scope

Implemented scaffold:

- MCQ dataset schema
- JSONL loader and validator
- prompt template loading
- exact-choice scorer
- deterministic constant model adapter for smoke tests
- result writer
- basic report command

Next useful steps:

- add an OpenAI-compatible model adapter
- add an Inspect AI runner
- add a SinhalaMMLU Hugging Face converter
- add per-subject/per-domain comparison reports
