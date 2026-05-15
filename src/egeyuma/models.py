from __future__ import annotations

from dataclasses import dataclass


class ModelAdapterError(Exception):
    """Raised when a model adapter cannot be created or used."""


@dataclass(frozen=True)
class ModelResponse:
    raw_response: str
    provider: str
    model: str


class ModelAdapter:
    provider: str
    model: str

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


def create_model_adapter(model_name: str) -> ModelAdapter:
    if model_name.startswith("constant/"):
        answer = model_name.split("/", maxsplit=1)[1].strip().upper()
        if answer not in {"A", "B", "C", "D", "E"}:
            raise ModelAdapterError("constant model must be one of constant/A ... constant/E")
        return ConstantModelAdapter(answer=answer)

    raise ModelAdapterError(
        f"Unsupported model {model_name!r}. Supported scaffold model: constant/A ... constant/E"
    )
