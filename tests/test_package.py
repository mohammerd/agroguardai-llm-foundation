from agroguardai import OpenAICompatibleAdapter, __version__


def test_package_version_is_defined():
    assert __version__ == "0.3.1"


def test_generic_hosted_adapter_is_public():
    assert OpenAICompatibleAdapter.__name__ == "OpenAICompatibleAdapter"
