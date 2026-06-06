# ============================================================
# Aviation Recovery Control Tower — Dockerfile
# ============================================================
# Multi-stage build using Google Distroless as final image.
#
# Stage 1 (builder): Alpine — installs deps and builds packages
# Stage 2 (runtime): gcr.io/distroless/python3 — zero shell,
#   no package manager, minimal CVE surface.
# ============================================================

# ============================================================
# STAGE 1 — BUILDER
# ============================================================
FROM python:3.12-alpine3.21 AS builder

# Build-time system deps
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libpq-dev \
    ca-certificates

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies into an isolated prefix
# so we can copy only that folder into the final image
COPY requirements.txt pyproject.toml ./
COPY src/ ./src/
COPY models/ ./models/
COPY config/ ./config/

RUN pip install --upgrade pip --no-cache-dir \
    && grep -vE \'^\ *(python[>=<]|#|$)\' requirements.txt \
       | grep -v \'^\ *-e\' \
       > /tmp/requirements_clean.txt \
    && pip install --no-cache-dir --prefix=/install -r /tmp/requirements_clean.txt \
    && pip install --no-cache-dir --prefix=/install .

# ============================================================
# STAGE 2 — DISTROLESS RUNTIME
# ============================================================
# gcr.io/distroless/python3-debian12 is maintained by Google,
# rebuilt nightly, and contains ONLY the Python interpreter +
# its minimal glibc runtime. No shell, no apt, no curl —
# drastically reduced CVE surface.
# ============================================================
FROM gcr.io/distroless/python3-debian12:nonroot

LABEL maintainer="immrm"
LABEL description="Aviation Recovery Control Tower — AI-driven disruption recovery platform"
LABEL python.version="3.12"

# Copy installed packages from builder
COPY --from=builder /install/lib /usr/local/lib
COPY --from=builder /install/bin /usr/local/bin

# Copy application source
WORKDIR /app
COPY --from=builder /app/ ./

# ============================================================
# RUNTIME ENVIRONMENT VARIABLES
# ============================================================
# Override at runtime via:
#   docker run --env-file .env ...
# or:
#   docker run -e GROQ_API_KEY=sk-... -e DB_HOST=... ...
# ============================================================
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/usr/local/lib/python3.12/site-packages:/app"

ENV DB_USER=""
ENV DB_PASSWORD=""
ENV DB_HOST=""
ENV DB_PORT="5432"
ENV DB_NAME=""
ENV GROQ_API_KEY=""

ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT="7860"

# ============================================================
# NON-ROOT USER
# ============================================================
# The distroless :nonroot tag runs as uid=65532 (nonroot)
# by default — no extra configuration needed.
# ============================================================

# ============================================================
# EXPOSE PORT
# ============================================================
EXPOSE 7860

# ============================================================
# ENTRYPOINT
# ============================================================
# Distroless has no shell, so CMD must use exec form (JSON array).
# python3 is the entrypoint provided by the distroless image.
# ============================================================
CMD ["app.py"]