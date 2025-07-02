# ── Dockerfile ──────────────────────────────────────────────────────────────
FROM python:3.11-slim

# 0. prevent Python from writing .pyc files & enable quicker stdout
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

# 1. copy project metadata  (needed for packaging)
COPY pyproject.toml README.md ./

# 2. copy the actual source *now* so it's available to the build backend
COPY src src

# 3. install the package (creates the 'phi-uploader' console script)
RUN pip install --no-cache-dir .

# 4. run as non-root for good measure
RUN useradd -m uploader
USER uploader

ENTRYPOINT ["phi-uploader"]     # default command inside the container
# ---------------------------------------------------------------------------

