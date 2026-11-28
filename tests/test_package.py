from agroguardai import (
    OpenAICompatibleAdapter,
    __version__,
    build_selected_adapter,
    load_model_config,
)


def test_package_version_is_defined():
    assert __version__ == "0.4.0"


def test_public_api_exports_provider_adapter_and_config_loader():
    assert OpenAICompatibleAdapter.__name__ == "OpenAICompatibleAdapter"
    assert callable(build_selected_adapter)
    assert callable(load_model_config)
