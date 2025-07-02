# ── Dockerfile ──────────────────────────────────────────────────────────────
FROM python:3.11-slim

# one layer per step keeps the image smaller thanks to cache re-use
WORKDIR /app

# 1. copy only metadata first (for layer caching)
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir .            # installs dependencies + console script

# 2. now copy the actual source code
COPY src/phi_uploader src/phi_uploader

ENTRYPOINT ["phi-uploader"]
# ---------------------------------------------------------------------------
