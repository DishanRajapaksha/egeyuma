from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from egeyuma.datasets.jsonl import DatasetValidationError
from egeyuma.datasets.schema import coerce_mcq_item

SINHALAMMLU_REPO = "naist-nlp/SinhalaMMLU"
SINHALAMMLU_REVISION = "main"
SINHALAMMLU_ALIASES = {
    "sinhalammlu",
    "sinhala-mmlu",
    "hf://naist-nlp/SinhalaMMLU",
    "naist-nlp/SinhalaMMLU",
    "https://huggingface.co/datasets/naist-nlp/SinhalaMMLU",
    "https://huggingface.co/datasets/naist-nlp/SinhalaMMLU/commits/main",
}
DEFAULT_CACHE_PATH = Path(".cache/egeyuma/sinhalammlu.jsonl")

FetchJson = Callable[[str, str | None], Any]


def resolve_dataset_path(
    dataset: str,
    *,
    refresh: bool = False,
    limit: int | None = None,
    cache_path: Path = DEFAULT_CACHE_PATH,
) -> Path:
    path = Path(dataset)
    if path.exists():
        return path

    if not is_sinhalammlu_ref(dataset):
        return path

    if cache_path.exists() and not refresh:
        return cache_path

    token = _hf_token()
    if not token:
        raise DatasetValidationError(
            f"{SINHALAMMLU_REPO} is restricted. Set HF_TOKEN to download it, "
            "or pass a local converted JSONL path."
        )

    materialize_sinhalammlu_dataset(cache_path, token=token, limit=limit)
    return cache_path


def is_sinhalammlu_ref(value: str) -> bool:
    return value.strip().rstrip("/") in SINHALAMMLU_ALIASES


def _hf_token(env_path: Path = Path(".env")) -> str | None:
    token = os.environ.get("HF_TOKEN")
    if token:
        return token

    if not env_path.exists():
        return None

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", maxsplit=1)
        if key.strip() == "HF_TOKEN":
            return value.strip().strip("'\"") or None

    return None


def materialize_sinhalammlu_dataset(
    output_path: Path,
    *,
    token: str,
    limit: int | None = None,
    fetch_json: FetchJson | None = None,
) -> int:
    fetch_json = fetch_json or _fetch_json
    records_written = 0
    tree = fetch_json(_tree_url(), token)
    json_paths = [
        entry["path"]
        for entry in tree
        if entry.get("type") == "file"
        and entry.get("path", "").startswith("TEST/")
        and entry.get("path", "").endswith(".json")
    ]
    if not json_paths:
        raise DatasetValidationError(f"No SinhalaMMLU JSON files found in {SINHALAMMLU_REPO}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for dataset_path in sorted(json_paths):
            payload = fetch_json(_raw_file_url(dataset_path), token)
            for raw_record in _iter_records(payload):
                raw_record = _with_source_file(raw_record, dataset_path)
                item = coerce_mcq_item(raw_record)
                handle.write(item.model_dump_json() + "\n")
                records_written += 1
                if limit is not None and records_written >= limit:
                    return records_written

    return records_written


def _with_source_file(raw_record: dict[str, Any], source_file: str) -> dict[str, Any]:
    metadata = dict(raw_record.get("metadata") or {})
    metadata.setdefault("hf_dataset", SINHALAMMLU_REPO)
    metadata.setdefault("hf_revision", SINHALAMMLU_REVISION)
    metadata.setdefault("hf_source_file", source_file)
    return {**raw_record, "metadata": metadata}


def _iter_records(payload: Any) -> Iterable[dict[str, Any]]:
    if isinstance(payload, list):
        for record in payload:
            if isinstance(record, dict):
                yield record
        return

    if isinstance(payload, dict):
        if {"q_no", "question", "choices", "answer"}.issubset(payload):
            yield payload
            return

        for key in ("data", "records", "questions", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                for record in value:
                    if isinstance(record, dict):
                        yield record
                return

    raise DatasetValidationError("Unsupported SinhalaMMLU JSON structure")


def _fetch_json(url: str, token: str | None) -> Any:
    headers = {"User-Agent": "egeyuma/0.1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise DatasetValidationError(f"Failed to fetch {url}: HTTP {exc.code}") from exc
    except URLError as exc:
        raise DatasetValidationError(f"Failed to fetch {url}: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise DatasetValidationError(f"Failed to parse JSON from {url}: {exc.msg}") from exc


def _tree_url() -> str:
    return (
        "https://huggingface.co/api/datasets/"
        f"{SINHALAMMLU_REPO}/tree/{SINHALAMMLU_REVISION}?recursive=true"
    )


def _raw_file_url(dataset_path: str) -> str:
    return (
        f"https://huggingface.co/datasets/{SINHALAMMLU_REPO}/resolve/"
        f"{SINHALAMMLU_REVISION}/{dataset_path}"
    )
