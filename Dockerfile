# Use the official Python image as a base
FROM python:3.11-slim

# Set a working directory
WORKDIR /app

# Copy only the metadata first (for better cache usage)
COPY pyproject.toml .

# Copy your source and other assets
COPY src/ ./src/
COPY notebooks/ ./notebooks/
COPY data/ ./data/

# Install your package (and deps) in editable mode, or normal mode
RUN pip install --upgrade pip \
 && pip install .

# Expose port & launch
EXPOSE 8000
CMD ["uvicorn", "notebook_service.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
