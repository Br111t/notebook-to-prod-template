## notebook-to-prod-template

Name: notebook-to-prod-template
Purpose: Template that turns a Jupyter notebook into a FastAPI microservice with CI, tests, and a Helm chart.

# Notebook-to-Prod Template

GitHub template for converting research notebooks into production-ready microservices.

## Features
- Template repo: boilerplate structure to start quickly.
- Notebook runner: FastAPI app serving notebook cells as endpoints.
- CI: Python 3.13 tests + linting.
- Helm chart: Kubernetes Deployment, Service, Ingress (optional), Secret, PVC.
- Codecov upload and optional Dependabot.

## Tech Stack
- Python: FastAPI + nbclient
- CI: GitHub Actions (Python 3.13) + coverage upload
- Container: Dockerfile with multi-stage build
- K8s: Helm v3 chart (`notebook-execution-service/`)

## Dependency Management
- Python dependencies are defined in `pyproject.toml`.
- Locking: use Poetry to generate and maintain `poetry.lock`.
  - Install Poetry (e.g., `pipx install poetry`).
  - Generate lockfile: `poetry lock`.
  - Optional: install with Poetry for local dev: `poetry install`.
- Dependabot is configured to open weekly PRs for Poetry, GitHub Actions, and Docker.

## Code Structure
```
notebook-to-prod-template/
  src/
    notebook_service/
      __init__.py
      cli.py                 # console-script entrypoint (notebook-cli)
      main.py                # FastAPI app (app = FastAPI())
      runner.py              # notebook execution logic (run_notebook)
      emotion.py             # emotion/concept/roles helpers
      graph_builder.py       # semantic-graph helpers
      schemas.py             # Pydantic models / response schemas
      visualization.py       # graph-plotting utilities
      config/
        dbpedia_exclusions.json

  notebooks/                 # example notebooks to execute
  data/                      # sample data files

  tests/
    conftest.py
    notebook_service/
      test_cli.py
      test_emotion.py
      test_runner.py
      test_graph_builder.py
      test_visualization.py
      test_main.py

  notebook-execution-service/  # Helm chart (Chart.yaml + templates/)
    Chart.yaml
    templates/
    values.yaml

  .github/workflows/ci.yml    # GitHub Actions: lint, test, build steps
  .pre-commit-config.yaml     # pre-commit (Black, Flake8, nbQA, etc.)
  docker-compose.yml          # local development runner
  Dockerfile                  # container build instructions
  pyproject.toml              # metadata, deps, build config, scripts
  README.md                   # overview, setup, usage, and structure
  LICENSE                     # license
  .gitignore
```

The concept-graph utilities live in `src/notebook_service/graph_builder.py`, with coverage in `tests/notebook_service/test_graph_builder.py`.

## Quick Start

1) Use as template
```bash
gh repo create my-project --template Br111t/notebook-to-prod-template
```

2) Edit notebook & endpoints

Update the sample notebook in `notebooks/` (e.g., `notebooks/example.ipynb`) and wire up endpoints in `src/notebook_service/` such as `main.py` and `runner.py`.

## CI & Deploy

Push changes and let GitHub Actions run:

```bash
git add .
git commit -m "Your meaningful commit message"

# when ready to cut a release
git tag v1.1.0
git describe --tags --exact-match
git push origin main --tags
```

| Bump type | Version change example | Meaning |
| --------- | ---------------------- | ------- |
| Patch     | 1.0.0 -> 1.0.1         | Bug fixes |
| Minor     | 1.0.1 -> 1.1.0         | Backward-compatible features |
| Major     | 1.1.0 -> 2.0.0         | Breaking changes |

## Testing & Linting

### Local workflow (no Docker)

```bash
# 1) Create and activate a virtual env
py -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# If you get an execution policy error:
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

With your venv activated:
```bash
# 2) Install the project (core + dev extras)
py -m pip install --upgrade pip setuptools
pip install -e ".[dev]"
# optional: vulnerability scan
# (install pip-audit via pipx to keep it isolated)
# pipx run pip-audit
```

Register your venv as a Jupyter kernel (optional):
```bash
py -m ipykernel install --sys-prefix --name notebook-to-prod --display-name "Python (notebook-to-prod)"
```

```bash
# 3) Lint & format (pre-commit runs all hooks)
pre-commit run --all-files
```

```bash
# 4) Run tests
pytest -q
pytest --cov=notebook_service --cov-report=term-missing
```

```bash
# 5) Run the FastAPI service
uvicorn notebook_service.main:app --reload
```

Swagger UI: http://localhost:8000/docs
ReDoc:      http://localhost:8000/redoc

### Using Docker
```bash
# 1) Build the image
docker build -t notebook-to-prod .

# 2) Run the container
docker run -p 8000:8000 --env-file .env notebook-to-prod

# 3) Run tests in the container (optional)
docker exec -it <container_id> pytest

# Tip: Expose docs explicitly
docker run -p 8000:8000 --env-file .env \
  notebook-to-prod uvicorn notebook_service.main:app --host 0.0.0.0
```
