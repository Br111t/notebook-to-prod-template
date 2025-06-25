# Stage 1: build environment
FROM python:3.12.2-slim AS builder
WORKDIR /app

# Install only what you need to build your wheel/packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: runtime
FROM python:3.12.2-slim
WORKDIR /app

# Pull in your installed dependencies
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy your application code
COPY app/ app/
COPY notebooks/ notebooks/

# (Optional) expose the port your app listens on
EXPOSE 8000

# Run your FastAPI service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
