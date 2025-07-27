############################
# 1) Builder stage
############################
FROM python:3.11-slim AS builder

# Install build‐time deps for SciPy / NumPy
RUN apt-get update -y \
 && apt-get install -y --no-install-recommends \
      git \
      build-essential \
      gcc \
      gfortran \
      libatlas-base-dev \
      libopenblas-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only what’s needed to install your package
COPY .git .git
COPY pyproject.toml .
COPY src/ src/
# (You don’t need notebooks or .git to build the wheel—omit for speed)

RUN pip install --upgrade pip \
 && pip install --editable .[dev]   \
 && rm -rf /root/.cache/pip

# Optional: run your tests here so your CI can catch breakages
# RUN pytest --maxfail=1 --disable-warnings --cov=src/notebook_service

############################
# 2) Runtime stage
############################
FROM python:3.11-slim

WORKDIR /app
ENV NOTEBOOK_DIR=/app/notebooks
ENV PYTHONPATH=/app/src

# Install runtime deps
RUN apt-get update -y \
 && apt-get install -y --no-install-recommends git curl \
 && rm -rf /var/lib/apt/lists/*

# Run as non-root for safety
RUN useradd --create-home appuser
USER appuser

# Pull in the installed package and its requirements
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/

# Copy your application code and notebooks
COPY src/ /app/src
COPY notebooks/ /app/notebooks/
COPY data/ /app/data/
COPY --chown=appuser:appuser data/ /app/data/

# Healthcheck for smoke‐tests
HEALTHCHECK --interval=30s --timeout=5s \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "notebook_service.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio"]
