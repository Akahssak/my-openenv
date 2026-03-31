# models.py
from typing import Optional, Dict, Any, Literal
from pydantic import Field
from openenv.core.env_server.types import Action, Observation


class InjectionDetectionAction(Action):
    """Agent's classification response for a prompt injection detection task."""
    is_injection: bool = Field(..., description="True if injection detected")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence 0.0-1.0")
    injection_type: Optional[str] = Field(
        None,
        description=(
            "e.g. 'direct_override', 'jailbreak_template', 'document_embedded', "
            "'unicode_tag', 'zero_width', 'homoglyph', 'base64_encoded', "
            "'emoji_smuggling', 'adversarial_suffix'"
        )
    )
    severity: Literal["none", "low", "medium", "high", "critical"] = Field(
        "none", description="Estimated severity of the injection"
    )
    explanation: Optional[str] = Field(
        None, description="Agent's reasoning (optional but rewards partial credit)"
    )


class InjectionDetectionObservation(Observation):
    """Environment observation: a text sample to classify."""
    sample_id: str = Field(..., description="Unique sample identifier")
    text: str = Field(..., description="The text to classify - may contain injection")
    source_type: str = Field(
        ...,
        description="'direct_input' | 'document' | 'api_response' | 'obfuscated'"
    )
    task_level: Literal["easy", "medium", "hard"] = Field(
        ..., description="Difficulty level of this sample"
    )
    context: Optional[str] = Field(
        None, description="Surrounding context if sample is embedded in a document"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Hints: file_type, encoding_present, source_dataset, step_num"
    )
