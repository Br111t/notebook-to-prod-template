
## 📦 4. `notebook-to-prod-template`
**Name:** `notebook-to-prod-template`
**Purpose:** Repo template that turns a Jupyter notebook into a FastAPI micro-service with CI, tests, and Helm chart.

# Notebook-to-Prod Template 📚➡️🚀

> GitHub template for converting research notebooks into production-ready microservices.

## 🚀 Features
- **Template repo:** boilerplate file structure & GitHub template link.
- **Notebook runner:** FastAPI app serving notebook cells as endpoints.
- **CI matrix:** test on multiple Python versions + linting.
- **Helm chart:** Kubernetes deployment with ConfigMap & Service.
- **Dependabot & Codecov** ready out of the box.

## 🛠️ Tech Stack
- **Python:** FastAPI + nbclient
- **CI:** GitHub Actions matrix build + coverage upload
- **Container:** Dockerfile + multi-stage build
- **K8s:** Helm v3 chart (`charts/notebook-to-prod`)


## Code Structure
```
notebook-to-prod-template/
├── src/
│   └── notebook_service/           ← your Python package
│       ├── __init__.py             # package marker
│       ├── cli.py                  # console‐script entrypoint (`notebook-cli`)
│       ├── main.py                 # FastAPI app (`app = FastAPI()`)
│       ├── runner.py               # notebook‐execution logic (`run_notebook`)
│       ├── emotion.py              # emotion‐analysis helper functions
│       ├── schemas.py              # Pydantic models / request‐response schemas
│       └── visualize.py
│
├── notebooks/                      # example Jupyter notebooks to execute
├── data/                           # sample data files consumed by notebooks
│
tests/
├── conftest.py                  # shared fixtures / test setup
├── notebook_service/
│    ├── test_cli.py             ← your CLI‐specific tests
│    ├── test_emotion.py         ← NLP/emotion extraction
│    ├── test_runner.py          ← core runner functions:
│    │     • load_data
│    │     • preprocess
│    │     • build_semantic_graph
│    │     • compute_centrality
│    ├── test_visualization.py   ← optional, smoke‐tests your graph‐plotting funcs
│    └── test_main.py            ← FastAPI endpoint tests
│
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions: lint, test, build steps
│
├── .pre-commit-config.yaml         # pre-commit hook definitions (Black, Flake8, etc.)
├── docker-compose.yml              # Compose file for spinning up service(s)
├── Dockerfile                      # container build instructions
├── pyproject.toml                  # PEP 621 metadata, deps, build config, scripts
├── README.md                       # overview, setup, usage, and project structure
├── LICENSE                         # your chosen open-source license
└── .gitignore                      # files/folders Git shouldn’t track

```

## 🚀 Quick Start

# 1. Use as template
```bash
gh repo create my-project --template Br111t/notebook-to-prod-template
```
# 2. Edit notebook & endpoints
Fill in `example.ipynb` and update `notebook_service.py`

## 3. CI & Deploy

Push your changes and let GitHub Actions take care of the rest:

```bash
git add .
# work, commit, push to main...
git commit -m "Your meaningful commit message"
# when ready to cut a release:
git tag v1.1.0
git push origin main --tags
# now:
pip install .       # or build your package
python -c "import pkg_resources; print(pkg_resources.get_distribution('notebook-to-prod-template').version)"
# → prints '1.1.0'

| Bump type | Version change example | What it signals                      |
| --------- | ---------------------- | ------------------------------------ |
| Patch     | `1.0.0 → 1.0.1`        | Bug fixes, no new features           |
| Minor     | `1.0.1 → 1.1.0`        | Backward-compatible new features     |
| Major     | `1.1.0 → 2.0.0`        | Breaking changes, drop support, etc. |


```

# 4. Testing locally vs. in Docker

🖥️ Local (without Docker)
```bash
# 1) Create a venv
python -m venv .venv

# 2) Activate it
source .venv/bin/activate        # macOS/Linux
.\.venv\Scripts\Activate.ps1     # Windows PowerShell
# if you hit an execution-policy error on Windows:
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# 3) Install your package (dev deps too, if desired)
pip install .[dev]              # includes pytest, flake8, etc.

# 4) Run tests
## Running Pre-commit Hooks & Tests
Before you commit, you can check code style and catch simple errors with **pre-commit**:

```bash
# Install pre-commit (if you haven't already):
pip install pre-commit

# Run all hooks against your staged files:
pre-commit run --all-files

# To run a specific hook, e.g. flake8:
pre-commit run flake8 --all-files
```

## To run your full test suite with pytest:
```bash
# From the repo root (venv activated if local):
pytest

# Show coverage report:
pytest --cov=notebook_service --cov-report=term-missing
```



# 5) Run your FastAPI service
```
uvicorn notebook_service.main:app --reload
```
FastAPI automatically mounts the interactive OpenAPI docs at:

Swagger UI:
http://127.0.0.1:8000/docs

ReDoc:
http://127.0.0.1:8000/redoc

🐳 Using Docker
# 1) Build the image
docker build -t notebook-to-prod .

# 2) Run the container
docker run -p 8000:8000 notebook-to-prod

# 3) Exec into container and run tests (optional)
docker exec -it <container_id> pytest

Tip: If you need the docs inside Docker, expose the host and port:
```bash
docker run -p 8000:8000 notebook-to-prod uvicorn notebook_service.main:app --host 0.0.0.0
```
