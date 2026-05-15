import pytest

from egeyuma.models import (
    ConstantModelAdapter,
    ModelAdapterError,
    OpenAICompatibleModelAdapter,
    create_model_adapter,
)


def test_create_constant_model_adapter() -> None:
    adapter = create_model_adapter("constant/B")

    assert isinstance(adapter, ConstantModelAdapter)
    assert adapter.generate("prompt").raw_response == "B"


def test_create_lmstudio_adapter_defaults() -> None:
    adapter = create_model_adapter("lmstudio/local-model")

    assert isinstance(adapter, OpenAICompatibleModelAdapter)
    assert adapter.provider == "lmstudio"
    assert adapter.model == "local-model"
    assert adapter.base_url == "http://localhost:1234/v1"
    assert adapter.api_key == "lm-studio"


def test_create_mistral_adapter_uses_mistral_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "mistral-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")

    adapter = create_model_adapter("mistral/mistral-small-latest")

    assert isinstance(adapter, OpenAICompatibleModelAdapter)
    assert adapter.provider == "mistral"
    assert adapter.base_url == "https://api.mistral.ai/v1"
    assert adapter.api_key == "mistral-key"


def test_openai_adapter_allows_overrides() -> None:
    adapter = create_model_adapter(
        "openai/gpt-4o-mini",
        base_url="http://localhost:8080/v1",
        api_key="local-key",
        temperature=0.2,
        max_tokens=8,
    )

    assert isinstance(adapter, OpenAICompatibleModelAdapter)
    assert adapter.base_url == "http://localhost:8080/v1"
    assert adapter.api_key == "local-key"
    assert adapter.temperature == 0.2
    assert adapter.max_tokens == 8


def test_rejects_unknown_model_provider() -> None:
    with pytest.raises(ModelAdapterError):
        create_model_adapter("unknown/model")
