# server/environment.py
import random
import uuid
from typing import Optional, Any

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State
from models import InjectionDetectionAction, InjectionDetectionObservation
from .dataset_loader import DatasetLoader
from .grader import grade_action


class PromptInjectionEnvironment(Environment):
    """
    OpenEnv environment for training agents to detect prompt injection attacks.

    Three task levels: easy (direct), medium (embedded), hard (obfuscated).
    Episode length: 10 samples. Mixed 60% injected / 40% clean per episode.
    """

    EPISODE_LENGTH = 10

    def __init__(self, task_level: str = "easy", seed: int = 42, **kwargs):
        super().__init__(**kwargs)
        self._task_level = task_level
        self._seed = seed
        self._loader = DatasetLoader(seed=seed)
        self._samples = self._loader.get_samples(task_level)
        self._state = State(episode_id=str(uuid.uuid4()), step_count=0)
        self._episode_samples = []
        self._current_sample = None
        self._episode_scores = []
        self._current_idx = 0
        self._episode_length = self.EPISODE_LENGTH
        # Auto-reset so the env is immediately ready for step() calls
        self.reset(seed=seed)

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> InjectionDetectionObservation:
        """Start a new 10-sample episode."""
        if seed is not None:
            self._seed = seed
        eid = episode_id or str(uuid.uuid4())
        self._state = State(episode_id=eid, step_count=0)
        self._episode_scores = []

        # Sample 10 items: ~60% injected, ~40% clean
        injected = [s for s in self._samples if s["label"] == 1]
        clean = [s for s in self._samples if s["label"] == 0]
        n_injected = 6
        n_clean = 4

        random.seed(self._seed + hash(self._state.episode_id) % 1000)

        # Use sampling with replacement if not enough samples
        if len(injected) >= n_injected:
            inj_chosen = random.sample(injected, n_injected)
        else:
            inj_chosen = random.choices(injected, k=n_injected) if injected else []

        if len(clean) >= n_clean:
            clean_chosen = random.sample(clean, n_clean)
        else:
            clean_chosen = random.choices(clean, k=n_clean) if clean else []

        chosen = inj_chosen + clean_chosen
        random.shuffle(chosen)

        # Adjust episode length to available samples (min 1)
        self._episode_length = min(self.EPISODE_LENGTH, max(len(chosen), 1))
        self._episode_samples = chosen[:self._episode_length]
        self._current_idx = 0

        return self._make_observation(self._episode_samples[0])

    def step(
        self,
        action: InjectionDetectionAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> InjectionDetectionObservation:
        """Score the action, advance to next sample."""
        current_sample = self._episode_samples[self._current_idx]
        score = grade_action(action, current_sample, self._task_level)
        self._episode_scores.append(score)

        self._state.step_count += 1
        self._current_idx += 1

        done = self._current_idx >= self._episode_length

        if done:
            # Return a terminal observation with final episode score
            obs = InjectionDetectionObservation(
                sample_id="episode_end",
                text="",
                source_type="direct_input",
                task_level=self._task_level,
                metadata={
                    "episode_score": sum(self._episode_scores) / len(self._episode_scores),
                    "step_scores": self._episode_scores,
                },
                done=True,
                reward=sum(self._episode_scores) / len(self._episode_scores),
            )
        else:
            next_sample = self._episode_samples[self._current_idx]
            obs = self._make_observation(next_sample)
            obs.reward = score
            obs.done = False

        return obs

    @property
    def state(self) -> State:
        return self._state

    def _make_observation(self, sample: dict) -> InjectionDetectionObservation:
        return InjectionDetectionObservation(
            sample_id=sample["sample_id"],
            text=sample["text"],
            source_type=sample.get("source_type", "direct_input"),
            task_level=self._task_level,
            context=sample.get("context"),
            metadata={
                "step": self._state.step_count + 1,
                "total_steps": self._episode_length,
                "source_dataset": sample.get("source_dataset", ""),
                # Provide a subtle hint for hard tasks so it's learnable
                "encoding_hint": sample.get("obfuscation_method", None)
                    if self._task_level == "hard" else None,
            },
            done=False,
            reward=0.0,
        )
