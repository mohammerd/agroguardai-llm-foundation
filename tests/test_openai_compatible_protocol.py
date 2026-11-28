from agroguardai import OpenAICompatibleAdapter, ProviderAdapter


def test_openai_compatible_adapter_implements_provider_protocol():
    adapter = OpenAICompatibleAdapter(
        provider_id="test-provider",
        base_url="https://api.example.test",
    )

    assert isinstance(adapter, ProviderAdapter)
    assert adapter.provider_id == "test-provider"
