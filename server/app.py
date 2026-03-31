# server/app.py
import os
import uvicorn
from openenv.core.env_server import create_app
from models import InjectionDetectionAction, InjectionDetectionObservation
from .environment import PromptInjectionEnvironment

# Read task level from env var so one Docker image serves all 3 tasks
TASK_LEVEL = os.getenv("TASK_LEVEL", "easy")
SEED = int(os.getenv("ENV_SEED", "42"))


def create_environment():
    """Factory: one isolated env instance per WebSocket session."""
    return PromptInjectionEnvironment(task_level=TASK_LEVEL, seed=SEED)


app = create_app(
    create_environment,
    InjectionDetectionAction,
    InjectionDetectionObservation,
    env_name="prompt-injection-detector",
)


@app.get("/")
def root():
    """Root endpoint for HuggingFace Spaces health check and discoverability."""
    return {
        "environment": "prompt-injection-detector",
        "version": "1.0.0",
        "description": "RL environment for training AI agents to detect prompt injection attacks",
        "task_level": TASK_LEVEL,
        "endpoints": {
            "health": "/health",
            "schema": "/schema",
            "reset": "POST /reset",
            "step": "POST /step",
        },
        "tasks": ["easy", "medium", "hard"],
        "status": "running",
    }


def main():
    """Entry point for running the environment server."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "server.app:app",
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
