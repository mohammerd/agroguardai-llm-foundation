from agroguardai import (
    HostedModelRuntime,
    OpenAICompatibleAdapter,
    __version__,
    build_selected_adapter,
    load_model_config,
)


def test_package_version_is_defined():
    assert __version__ == "0.5.0"


def test_public_api_exports_provider_and_runtime_components():
    assert OpenAICompatibleAdapter.__name__ == "OpenAICompatibleAdapter"
    assert HostedModelRuntime.__name__ == "HostedModelRuntime"
    assert callable(build_selected_adapter)
    assert callable(load_model_config)
