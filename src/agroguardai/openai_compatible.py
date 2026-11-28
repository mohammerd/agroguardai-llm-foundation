"""Generic hosted adapter for OpenAI-compatible chat-completions APIs.

This adapter implements the project's initial text-only generation contract.
Provider-specific capabilities must be discovered and verified separately.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse

import httpx

from .errors import (
    ConfigurationError,
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderProtocolError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderRequestMismatchError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from .models import (
    GenerationRequest,
    GenerationResponse,
    ModelDescriptor,
    Modality,
    Operation,
    TermsStatus,
    validate_provider_response,
)


class OpenAICompatibleAdapter:
    """Hosted adapter for providers with compatible model-list and chat routes.

    The caller supplies a stable provider ID, API base URL, and optional key.
    The base URL may include a version prefix, for example the OpenRouter
    API prefix. Credentials are held only in memory and are never logged.
    """

    def __init__(
        self,
        *,
        provider_id: str,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 30.0,
        model_list_path: str = "models",
        chat_completions_path: str = "chat/completions",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ConfigurationError("provider_id must be a non-empty string.")
        if provider_id != provider_id.strip() or any(c.isspace() for c in provider_id):
            raise ConfigurationError("provider_id must not contain whitespace.")
        if not isinstance(base_url, str):
            raise ConfigurationError("base_url must be an absolute HTTP(S) URL.")
        parsed = urlparse(base_url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise ConfigurationError("base_url must be an absolute HTTP(S) URL.")
        if parsed.username is not None or parsed.password is not None:
            raise ConfigurationError("base_url must not contain embedded credentials.")
        if parsed.scheme != "https" and parsed.hostname not in {
            "localhost",
            "127.0.0.1",
            "::1",
        }:
            raise ConfigurationError("Non-local provider endpoints must use HTTPS.")
        if parsed.query or parsed.fragment:
            raise ConfigurationError("base_url must not include a query string or fragment.")
        if api_key is not None and (not isinstance(api_key, str) or not api_key.strip()):
            raise ConfigurationError("api_key must be a non-empty string or None.")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ConfigurationError("timeout must be a positive number of seconds.")

        for field_name, path in (
            ("model_list_path", model_list_path),
            ("chat_completions_path", chat_completions_path),
        ):
            if (
                not isinstance(path, str)
                or not path.strip()
                or path.startswith("/")
                or "://" in path
                or "?" in path
                or "#" in path
                or "\\" in path
                or any(part in {".", ".."} for part in path.split("/"))
                or any(character.isspace() for character in path)
            ):
                raise ConfigurationError(
                    f"{field_name} must be a safe relative API path."
                )

        self._provider_id = provider_id
        self._base_url = base_url.rstrip("/") + "/"
        self._api_key = api_key
        self._timeout = float(timeout)
        self._model_list_path = model_list_path
        self._chat_completions_path = chat_completions_path
        self._client = client

    @property
    def provider_id(self) -> str:
        """Return the stable provider identifier."""

        return self._provider_id

    @classmethod
    def from_env(
        cls,
        *,
        api_key_env: str,
        **kwargs: Any,
    ) -> OpenAICompatibleAdapter:
        """Construct an adapter using a credential from a named environment variable."""

        if not isinstance(api_key_env, str) or not api_key_env.strip():
            raise ConfigurationError("api_key_env must name a non-empty environment variable.")
        if "api_key" in kwargs:
            raise ConfigurationError("Use api_key_env or api_key, not both.")
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ConfigurationError(
                f"Required provider credential environment variable '{api_key_env}' is not set."
            )
        return cls(api_key=api_key, **kwargs)

    async def discover_models(self) -> tuple[ModelDescriptor, ...]:
        """Fetch the model catalog and return only explicitly advertised text models.

        Model catalogs differ. The adapter accepts top-level input/output modality
        fields or the OpenRouter-style architecture.input_modalities/output_modalities
        fields. Models without explicit text support are not registered by this
        text-only adapter; they can be handled by a future modality-specific adapter.
        """

        response = await self._request("GET", self._model_list_path)
        payload = self._decode_json(response, "model catalog")
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            raise ProviderProtocolError(
                f"Provider '{self.provider_id}' returned an invalid model catalog."
            )

        descriptors: list[ModelDescriptor] = []
        seen_ids: set[str] = set()
        for index, item in enumerate(payload["data"]):
            if not isinstance(item, dict):
                raise ProviderProtocolError(
                    f"Provider '{self.provider_id}' catalog item {index} is not an object."
                )
            model_id = item.get("id")
            if not isinstance(model_id, str) or not model_id.strip():
                raise ProviderProtocolError(
                    f"Provider '{self.provider_id}' catalog item {index} has no valid model ID."
                )
            if model_id in seen_ids:
                raise ProviderProtocolError(
                    f"Provider '{self.provider_id}' returned duplicate model ID '{model_id}'."
                )
            seen_ids.add(model_id)

            architecture = item.get("architecture")
            architecture = architecture if isinstance(architecture, dict) else {}
            input_modalities = item.get(
                "input_modalities", architecture.get("input_modalities")
            )
            output_modalities = item.get(
                "output_modalities", architecture.get("output_modalities")
            )
            if not self._advertises_text(input_modalities) or not self._advertises_text(
                output_modalities
            ):
                continue

            display_name = item.get("name")
            if not isinstance(display_name, str) or not display_name.strip():
                display_name = model_id

            descriptors.append(
                ModelDescriptor(
                    provider_id=self.provider_id,
                    model_id=model_id,
                    display_name=display_name,
                    operations=frozenset({Operation.HOSTED_INFERENCE}),
                    input_modalities=frozenset({Modality.TEXT}),
                    output_modalities=frozenset({Modality.TEXT}),
                    context_window=self._context_window(item),
                    terms_status=TermsStatus.UNREVIEWED,
                    available=True,
                )
            )

        return tuple(descriptors)

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Call the exact selected model through the chat-completions route."""

        if request.selection.provider_id != self.provider_id:
            raise ProviderRequestMismatchError(
                f"Adapter '{self.provider_id}' cannot execute a request for provider "
                f"'{request.selection.provider_id}'."
            )
        if request.selection.operation is not Operation.HOSTED_INFERENCE:
            raise ProviderRequestMismatchError(
                "OpenAICompatibleAdapter supports hosted_inference only."
            )

        body: dict[str, Any] = {
            "model": request.selection.model_id,
            "messages": [
                {"role": message.role.value, "content": message.content}
                for message in request.messages
            ],
            "stream": False,
        }
        if request.max_output_tokens is not None:
            body["max_tokens"] = request.max_output_tokens
        if request.temperature is not None:
            body["temperature"] = request.temperature

        response = await self._request("POST", self._chat_completions_path, json=body)
        payload = self._decode_json(response, "chat completion")
        if not isinstance(payload, dict):
            raise ProviderProtocolError(
                f"Provider '{self.provider_id}' returned an invalid chat-completion response."
            )

        returned_model = payload.get("model")
        choices = payload.get("choices")
        if not isinstance(returned_model, str) or not isinstance(choices, list) or not choices:
            raise ProviderProtocolError(
                f"Provider '{self.provider_id}' response is missing model or choices."
            )
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise ProviderProtocolError(
                f"Provider '{self.provider_id}' returned an invalid first choice."
            )
        message = first_choice.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ProviderProtocolError(
                f"Provider '{self.provider_id}' returned non-text or missing message content."
            )

        finish_reason = first_choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            raise ProviderProtocolError(
                f"Provider '{self.provider_id}' returned an invalid finish reason."
            )

        usage = payload.get("usage")
        if usage is not None and not isinstance(usage, dict):
            raise ProviderProtocolError(
                f"Provider '{self.provider_id}' returned invalid usage metadata."
            )
        input_tokens = self._usage_count(usage, "prompt_tokens") if usage else None
        output_tokens = self._usage_count(usage, "completion_tokens") if usage else None

        result = GenerationResponse(
            provider_id=self.provider_id,
            model_id=returned_model,
            output_text=message["content"],
            finish_reason=finish_reason,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        validate_provider_response(request, result)
        return result

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        headers = {"Accept": "application/json"}
        if json is not None:
            headers["Content-Type"] = "application/json"
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        url = self._base_url + path

        try:
            if self._client is not None:
                response = await self._client.request(
                    method,
                    url,
                    headers=headers,
                    json=json,
                    timeout=self._timeout,
                )
            else:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.request(
                        method,
                        url,
                        headers=headers,
                        json=json,
                    )
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                f"Provider '{self.provider_id}' request timed out."
            ) from exc
        except httpx.RequestError as exc:
            raise ProviderConnectionError(
                f"Could not connect to provider '{self.provider_id}'."
            ) from exc

        if response.status_code in {401, 403}:
            raise ProviderAuthenticationError(
                f"Provider '{self.provider_id}' rejected authentication "
                f"(HTTP {response.status_code})."
            )
        if response.status_code == 429:
            raise ProviderRateLimitError(
                f"Provider '{self.provider_id}' rate-limited the request (HTTP 429)."
            )
        if response.status_code >= 500:
            raise ProviderUnavailableError(
                f"Provider '{self.provider_id}' returned HTTP {response.status_code}."
            )
        if response.is_error:
            raise ProviderRequestError(
                f"Provider '{self.provider_id}' rejected the request "
                f"(HTTP {response.status_code})."
            )
        return response

    def _decode_json(self, response: httpx.Response, response_name: str) -> Any:
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderProtocolError(
                f"Provider '{self.provider_id}' returned invalid JSON for {response_name}."
            ) from exc

    @staticmethod
    def _advertises_text(modalities: Any) -> bool:
        return isinstance(modalities, list) and "text" in modalities

    @staticmethod
    def _context_window(item: Mapping[str, Any]) -> int | None:
        value = item.get("context_window", item.get("context_length"))
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ProviderProtocolError("Provider returned an invalid context-window value.")
        return value

    @staticmethod
    def _usage_count(usage: Mapping[str, Any], key: str) -> int | None:
        value = usage.get(key)
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ProviderProtocolError(f"Provider returned invalid usage field '{key}'.")
        return value
