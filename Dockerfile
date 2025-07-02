# ---- Dockerfile ----------------------------------------------------------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# 1. project metadata (allows layer-caching for deps)
COPY pyproject.toml README.md ./

# 2. project source *before* installation
COPY src/ src/

# 3. install; this drops the console-script into /usr/local/bin/
RUN pip install --no-cache-dir .

# 4. non-root user (optional safety)
RUN useradd -m uploader
USER uploader

# JSON form ⇒ extra words are appended (phi-uploader build …)
ENTRYPOINT ["phi-uploader"]
