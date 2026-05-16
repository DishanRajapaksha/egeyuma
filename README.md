# ඇගැයුම - Egeyuma

## Engine

```bash
cd engine
uv sync --all-extras --dev
```

```bash
cd engine
uv run egeyuma validate ../data/samples/sinhalammlu_sample.jsonl
```

```bash
cd engine
uv run egeyuma run \
  --dataset ../data/samples/sinhalammlu_sample.jsonl \
  --model constant/B \
  --prompt mcq_si_subject_v1 \
  --output ../results/sample-run.json
```

```bash
cd engine
uv run egeyuma run \
  --dataset sinhalammlu \
  --dataset-limit 100 \
  --model constant/B \
  --prompt mcq_si_subject_v1 \
  --output ../results/sinhalammlu-100.json
```

```bash
cd engine
uv run egeyuma run \
  --dataset sinhalammlu \
  --model lmstudio/google/gemma-4-e4b \
  --base-url http://192.168.1.4:1234/v1 \
  --api-key lm-studio \
  --prompt mcq_si_subject_v1 \
  --max-tokens 2048 \
  --output ../results/gemma-4-e4b-lmstudio-sinhalammlu.json
```

```bash
cd engine
uv run egeyuma report ../results/sample-run.json
```

```bash
cd engine
uv run ruff check .
uv run mypy src tests
uv run pytest
```

## Dashboard

```bash
cd dashboard
npm install
npm run dev
```

```bash
cd dashboard
npm run check
npm run build
```

## Docs

```bash
open engine/docs/README.md
open dashboard/docs/README.md
```

```bash
cd docs-site
npm install
npm run start
```

```bash
cd docs-site
npm run build
```
