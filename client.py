# client.py
from openenv.core.env_client import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State
from models import InjectionDetectionAction, InjectionDetectionObservation


class PromptInjectionEnv(EnvClient[
    InjectionDetectionAction,
    InjectionDetectionObservation,
    State
]):
    """Client for the PromptInjectionDetector environment."""

    def _step_payload(self, action: InjectionDetectionAction) -> dict:
        return {
            "is_injection": action.is_injection,
            "confidence": action.confidence,
            "injection_type": action.injection_type,
            "severity": action.severity,
            "explanation": action.explanation,
        }

    def _parse_result(self, payload: dict) -> StepResult[InjectionDetectionObservation]:
        obs_data = payload.get("observation", {})
        obs = InjectionDetectionObservation(
            sample_id=obs_data.get("sample_id", ""),
            text=obs_data.get("text", ""),
            source_type=obs_data.get("source_type", "direct_input"),
            task_level=obs_data.get("task_level", "easy"),
            context=obs_data.get("context"),
            metadata=obs_data.get("metadata", {}),
            done=payload.get("done", False),
            reward=payload.get("reward", 0.0),
        )
        return StepResult(
            observation=obs,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict) -> State:
        return State(
            episode_id=payload.get("episode_id", ""),
            step_count=payload.get("step_count", 0),
        )
