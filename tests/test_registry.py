import pytest

from agroguardai.errors import (
    DuplicateModelError,
    ModelTermsError,
    ModelUnavailableError,
    ProviderIdentityMismatchError,
    UnknownModelError,
    UnknownProviderError,
    UnsupportedOperationError,
)
from agroguardai.models import ModelDescriptor, ModelSelection, Operation, TermsStatus
from agroguardai.registry import ModelRegistry


def descriptor(
    *,
    provider_id: str = "local",
    model_id: str = "orchard-7b",
    operations: frozenset[Operation] | None = None,
    terms_status: TermsStatus = TermsStatus.REVIEWED,
    available: bool = True,
) -> ModelDescriptor:
    return ModelDescriptor(
        provider_id=provider_id,
        model_id=model_id,
        display_name=model_id,
        operations=operations
        or frozenset({Operation.LOCAL_INFERENCE, Operation.FINE_TUNING}),
        terms_status=terms_status,
        available=available,
    )


def selection(
    *,
    provider_id: str = "local",
    model_id: str = "orchard-7b",
    operation: Operation = Operation.LOCAL_INFERENCE,
) -> ModelSelection:
    return ModelSelection(
        provider_id=provider_id,
        model_id=model_id,
        operation=operation,
    )


def test_registry_resolves_exact_provider_and_model():
    registry = ModelRegistry()
    expected = descriptor()
    registry.register(expected)

    assert registry.resolve(selection()) is expected


def test_unknown_provider_fails_without_substitution():
    registry = ModelRegistry()
    registry.register(descriptor())

    with pytest.raises(UnknownProviderError, match="no alternative provider"):
        registry.resolve(selection(provider_id="unknown"))


def test_unknown_model_fails_without_substitution():
    registry = ModelRegistry()
    registry.register(descriptor())

    with pytest.raises(UnknownModelError, match="No substitute"):
        registry.resolve(selection(model_id="different-model"))


def test_unavailable_model_fails():
    registry = ModelRegistry()
    registry.register(descriptor(available=False))

    with pytest.raises(ModelUnavailableError):
        registry.resolve(selection())


def test_unsupported_operation_fails():
    registry = ModelRegistry()
    registry.register(descriptor(operations=frozenset({Operation.LOCAL_INFERENCE})))

    with pytest.raises(UnsupportedOperationError):
        registry.resolve(selection(operation=Operation.FINE_TUNING))


def test_fine_tuning_is_blocked_until_terms_review():
    registry = ModelRegistry()
    registry.register(
        descriptor(
            terms_status=TermsStatus.UNREVIEWED,
            operations=frozenset({Operation.LOCAL_INFERENCE, Operation.FINE_TUNING}),
        )
    )

    with pytest.raises(ModelTermsError, match="blocked until"):
        registry.resolve(selection(operation=Operation.FINE_TUNING))


def test_restricted_model_cannot_be_used():
    registry = ModelRegistry()
    registry.register(descriptor(terms_status=TermsStatus.RESTRICTED))

    with pytest.raises(ModelTermsError, match="restricted"):
        registry.resolve(selection())


def test_duplicate_registration_does_not_overwrite():
    registry = ModelRegistry()
    original = descriptor()
    registry.register(original)

    with pytest.raises(DuplicateModelError):
        registry.register(descriptor())

    assert registry.resolve(selection()) is original


def test_register_many_is_atomic_when_batch_contains_duplicates():
    registry = ModelRegistry()
    first = descriptor()
    second = descriptor(model_id="second")

    with pytest.raises(DuplicateModelError):
        registry.register_many([first, first])

    assert registry.list_models() == ()

    registry.register_many([first, second])
    assert [item.model_id for item in registry.list_models()] == ["orchard-7b", "second"]


def test_provider_catalog_rejects_mismatched_provider_identity_atomically():
    registry = ModelRegistry()

    with pytest.raises(ProviderIdentityMismatchError):
        registry.register_provider_catalog("provider-a", [descriptor(provider_id="provider-b")])

    assert registry.provider_ids == ()
    assert registry.list_models() == ()


def test_empty_provider_catalog_is_distinct_from_unknown_provider():
    registry = ModelRegistry()
    registry.register_provider_catalog("empty-provider", [])

    assert registry.provider_ids == ("empty-provider",)
    with pytest.raises(UnknownModelError, match="No substitute"):
        registry.resolve(selection(provider_id="empty-provider", model_id="not-listed"))
