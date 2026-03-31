"""Test all three difficulty levels."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
from server.environment import PromptInjectionEnvironment
from models import InjectionDetectionAction

for level in ["easy", "medium", "hard"]:
    env = PromptInjectionEnvironment(task_level=level, seed=42)
    obs = env.reset()
    scores = []
    
    print(f"\n{'='*60}")
    print(f"  LEVEL: {level.upper()} | Episode length: {env._episode_length}")
    print(f"{'='*60}")
    print(f"  First sample: {obs.text[:60]}...")
    
    for i in range(env._episode_length):
        # Simple heuristic: classify as injection if suspicious keywords found
        text_lower = obs.text.lower()
        is_inj = any(kw in text_lower for kw in ['ignore', 'forget', 'override', 'bypass', 'jailbreak', 'dan', 'unrestricted', 'no rules', 'hack'])
        
        action = InjectionDetectionAction(
            is_injection=is_inj,
            confidence=0.8 if is_inj else 0.7,
            injection_type="direct_override" if is_inj and level == "easy" else ("document_embedded" if is_inj and level == "medium" else ("unicode_tag" if is_inj else None)),
            severity="high" if is_inj else "none",
            explanation=f"{'Detected' if is_inj else 'No'} injection indicators found in the text"
        )
        obs = env.step(action)
        scores.append(obs.reward if not obs.done else (obs.metadata.get('episode_score', 0)))
        
        if obs.done:
            ep_score = obs.metadata.get('episode_score', sum(scores)/len(scores))
            print(f"  Steps: {i+1} | Episode Score: {ep_score:.3f}")
            print(f"  Step scores: {[f'{s:.2f}' for s in obs.metadata.get('step_scores', scores)]}")
            break

print(f"\n{'='*60}")
print("  ALL LEVELS TESTED SUCCESSFULLY")
print(f"{'='*60}")
