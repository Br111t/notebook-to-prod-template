FROM python:3.11-slim

RUN apt-get update -y \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV NOTEBOOK_DIR=/app/notebooks

# Copy *only* the files needed to build the wheel, including .git
COPY .git .git
COPY pyproject.toml ./
COPY src/ src/
COPY notebooks/ ./notebooks/

RUN pip install --upgrade pip \
 && pip install --editable . \
 && rm -rf .git

# Remaining files (tests, notebooks, docs, etc.) — won't bust the cache
COPY . .

EXPOSE 8000
CMD ["uvicorn", "notebook_service.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio"]
