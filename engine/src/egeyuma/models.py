from __future__ import annotations

import os
from dataclasses import dataclass
from importlib import import_module
from typing import Any, cast


class ModelAdapterError(Exception):
    """Raised when a model adapter cannot be created or used."""


@dataclass(frozen=True)
class ModelResponse:
    raw_response: str
    provider: str
    model: str


class ModelAdapter:
    def generate(self, prompt: str) -> ModelResponse:
        raise NotImplementedError


@dataclass(frozen=True)
class ConstantModelAdapter(ModelAdapter):
    """Deterministic smoke-test adapter.

    Example model name: constant/B
    """

    answer: str
    provider: str = "constant"

    @property
    def model(self) -> str:
        return self.answer

    def generate(self, prompt: str) -> ModelResponse:
        return ModelResponse(raw_response=self.answer, provider=self.provider, model=self.model)


@dataclass(frozen=True)
class OpenAICompatibleModelAdapter(ModelAdapter):
    """OpenAI Chat Completions compatible adapter.

    Works with OpenAI, Mistral's OpenAI-compatible endpoint, and local servers
    such as LM Studio that expose `/v1/chat/completions`.
    """

    model_id: str
    provider: str
    base_url: str | None
    api_key: str | None
    temperature: float
    max_tokens: int

    @property
    def model(self) -> str:
        return self.model_id

    def generate(self, prompt: str) -> ModelResponse:
        try:
            openai_module = import_module("openai")
        except ImportError as exc:
            raise ModelAdapterError(
                "OpenAI-compatible models require the optional dependency: "
                "pip install -e '.[openai]'"
            ) from exc

        openai_client = cast(Any, openai_module).OpenAI
        client_kwargs: dict[str, Any] = {}
        if self.api_key is not None:
            client_kwargs["api_key"] = self.api_key
        if self.base_url is not None:
            client_kwargs["base_url"] = self.base_url

        try:
            client = openai_client(**client_kwargs)
            completion = client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except Exception as exc:  # pragma: no cover - SDK exception types vary by version/provider.
            raise ModelAdapterError(f"{self.provider} model request failed: {exc}") from exc

        content = completion.choices[0].message.content
        if not isinstance(content, str):
            raise ModelAdapterError(f"{self.provider} returned an empty or non-text response")

        return ModelResponse(raw_response=content.strip(), provider=self.provider, model=self.model)


def _env_first(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def _openai_compatible_defaults(provider: str) -> tuple[str | None, str | None]:
    if provider == "mistral":
        return "https://api.mistral.ai/v1", _env_first("MISTRAL_API_KEY", "OPENAI_API_KEY")
    if provider == "lmstudio":
        api_key = _env_first("LMSTUDIO_API_KEY", "OPENAI_API_KEY") or "lm-studio"
        return "http://localhost:1234/v1", api_key
    if provider == "openai":
        return _env_first("OPENAI_BASE_URL"), _env_first("OPENAI_API_KEY")

    return _env_first("OPENAI_BASE_URL"), _env_first("OPENAI_API_KEY")


def create_model_adapter(
    model_name: str,
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 16,
) -> ModelAdapter:
    if model_name.startswith("constant/"):
        answer = model_name.split("/", maxsplit=1)[1].strip().upper()
        if answer not in {"A", "B", "C", "D", "E"}:
            raise ModelAdapterError("constant model must be one of constant/A ... constant/E")
        return ConstantModelAdapter(answer=answer)

    if "/" in model_name:
        provider, model_id = model_name.split("/", maxsplit=1)
        provider = provider.strip().lower()
        model_id = model_id.strip()
        if provider in {"openai", "mistral", "lmstudio"} and model_id:
            default_base_url, default_api_key = _openai_compatible_defaults(provider)
            return OpenAICompatibleModelAdapter(
                model_id=model_id,
                provider=provider,
                base_url=base_url or default_base_url,
                api_key=api_key or default_api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )

    raise ModelAdapterError(
        f"Unsupported model {model_name!r}. Supported models: constant/A ... constant/E, "
        "openai/<model>, mistral/<model>, lmstudio/<model>"
    )
