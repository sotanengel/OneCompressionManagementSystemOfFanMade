import pytest
from pydantic import ValidationError

from ocms.api.schemas import JobCreateRequest, QuantMethod


def test_valid_gptq_int4() -> None:
    req = JobCreateRequest(
        model_id="meta-llama/Llama-3.1-8B",
        quant_method=QuantMethod.GPTQ,
        bits=4,
        instance_type="g5.xlarge",
    )
    assert req.quant_method == QuantMethod.GPTQ
    assert req.bits == 4
    assert req.region == "us-east-1"
    assert req.spot is False
    assert req.feature_flags.check_env_preflight is False


def test_fp8_requires_bits_8() -> None:
    with pytest.raises(ValidationError, match="FP8"):
        JobCreateRequest(
            model_id="meta-llama/Llama-3.1-8B",
            quant_method=QuantMethod.FP8,
            bits=4,
            instance_type="g5.xlarge",
        )


def test_fp8_with_bits_8_passes() -> None:
    req = JobCreateRequest(
        model_id="meta-llama/Llama-3.1-8B",
        quant_method=QuantMethod.FP8,
        bits=8,
        instance_type="g5.xlarge",
    )
    assert req.bits == 8


def test_bits_must_be_between_4_and_8() -> None:
    with pytest.raises(ValidationError):
        JobCreateRequest(
            model_id="meta-llama/Llama-3.1-8B",
            quant_method=QuantMethod.GPTQ,
            bits=2,
            instance_type="g5.xlarge",
        )


def test_invalid_quant_method_raises() -> None:
    with pytest.raises(ValidationError):
        JobCreateRequest(
            model_id="meta-llama/Llama-3.1-8B",
            quant_method="INVALID",  # type: ignore[arg-type]
            bits=4,
            instance_type="g5.xlarge",
        )


def test_feature_flags_can_be_set() -> None:
    from ocms.api.schemas import FeatureFlagsRequest

    req = JobCreateRequest(
        model_id="meta-llama/Llama-3.1-8B",
        quant_method=QuantMethod.GPTQ,
        bits=4,
        instance_type="g5.xlarge",
        feature_flags=FeatureFlagsRequest(check_env_preflight=True, checkpoint=True),
    )
    assert req.feature_flags.check_env_preflight is True
    assert req.feature_flags.checkpoint is True


def test_max_runtime_hours_default() -> None:
    req = JobCreateRequest(
        model_id="meta-llama/Llama-3.1-8B",
        quant_method=QuantMethod.GPTQ,
        bits=4,
        instance_type="g5.xlarge",
    )
    assert req.max_runtime_hours == 4
