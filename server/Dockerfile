# server/Dockerfile
ARG BASE_IMAGE=openenv-base:latest
FROM ${BASE_IMAGE} AS builder

WORKDIR /app
ARG BUILD_MODE=in-repo
ARG ENV_NAME=prompt-injection-detector

# Copy environment code
COPY . /app/env
WORKDIR /app/env

# Install with uv (lock file preferred)
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -f uv.lock ]; then \
        uv sync --frozen --no-install-project --no-editable; \
    else \
        uv sync --no-install-project --no-editable; \
    fi

RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -f uv.lock ]; then \
        uv sync --frozen --no-editable; \
    else \
        uv sync --no-editable; \
    fi

FROM ${BASE_IMAGE}

WORKDIR /app

COPY --from=builder /app/env/.venv /app/.venv
COPY --from=builder /app/env /app/env

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/env:$PYTHONPATH"
ENV TASK_LEVEL="easy"

# Pre-download and cache HuggingFace datasets at build time
RUN python -c "\
from server.dataset_loader import DatasetLoader; \
loader = DatasetLoader(seed=42); \
[print(f'{level}: {len(loader.get_samples(level))} samples loaded') for level in ['easy', 'medium', 'hard']]" \
    || echo "Dataset pre-load failed - will load at runtime"

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
