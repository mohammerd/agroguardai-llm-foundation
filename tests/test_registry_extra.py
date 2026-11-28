import pytest

from agroguardai.errors import ModelTermsError
from agroguardai.models import ModelDescriptor, ModelSelection, Operation, TermsStatus
from agroguardai.registry import ModelRegistry


def test_unreviewed_model_can_run_inference_but_not_export_weights():
    registry = ModelRegistry()
    registry.register(
        ModelDescriptor(
            provider_id="local",
            model_id="research-checkpoint",
            display_name="Research checkpoint",
            operations=frozenset({Operation.LOCAL_INFERENCE, Operation.WEIGHT_EXPORT}),
            terms_status=TermsStatus.UNREVIEWED,
        )
    )

    inference = registry.resolve(
        ModelSelection("local", "research-checkpoint", Operation.LOCAL_INFERENCE)
    )
    assert inference.model_id == "research-checkpoint"

    with pytest.raises(ModelTermsError, match="blocked until"):
        registry.resolve(
            ModelSelection("local", "research-checkpoint", Operation.WEIGHT_EXPORT)
        )


def test_descriptor_accepts_single_operation_string_and_normalizes_it():
    descriptor = ModelDescriptor(
        provider_id="hosted",
        model_id="chat-model",
        display_name="Chat model",
        operations="hosted_inference",
    )

    assert descriptor.operations == frozenset({Operation.HOSTED_INFERENCE})
