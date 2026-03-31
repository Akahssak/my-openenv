FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY server/requirements.txt /app/server/requirements.txt
RUN pip install --no-cache-dir -r /app/server/requirements.txt

# Copy all project files
COPY . /app/

# Set environment
ENV PYTHONPATH="/app:$PYTHONPATH"
ENV PYTHONUNBUFFERED=1
ENV TASK_LEVEL="easy"
ENV HOST="0.0.0.0"
ENV PORT="7860"

# Pre-load datasets into cache
RUN python -c "\
from server.dataset_loader import DatasetLoader; \
loader = DatasetLoader(seed=42); \
[print(f'{level}: {len(loader.get_samples(level))} samples loaded') for level in ['easy', 'medium', 'hard']]" \
    || echo 'Dataset pre-load used fallback data'

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
