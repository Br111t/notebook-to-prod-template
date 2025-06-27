
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
notebook-to-prod/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app
│   ├── runner.py         # notebook-execution logic
├── notebooks/
│   └── example.ipynb
├── tests/
│   ├── test_runner.py
│   └── test_main.py
├── requirements.txt
├── Dockerfile
└── .github/
    └── workflows/ci.yml
```

## 🚀 Quick Start

# 1. Use as template
```bash
gh repo create my-project --template Br111t/notebook-to-prod-template
```
# 2. Edit notebook & endpoints
Fill in `example.ipynb` and update `notebook_service.py`

# 3. CI & deploy
git push && watch GitHub Actions run your tests + build + (optional) Helm install


# 4. Testing locally vs. in Docker

Locally (without Docker), you’ll run:
```bash
python3 -m venv .venv       # create a virtualenv
source .venv/bin/activate   # on Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

In Docker, you’ll do:

```bash
docker build -t notebook-to-prod .
docker run -p 8000:8000 notebook-to-prod
```
