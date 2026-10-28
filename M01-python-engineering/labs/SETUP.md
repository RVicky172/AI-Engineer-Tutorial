# M01 Lab Environment Setup

## Prerequisites
- Python 3.12+
- git
- An editor with Python + Ruff extensions
- Optional: [uv](https://docs.astral.sh/uv/) (`brew install uv`), a faster pip/venv replacement

## Python environment (one shared venv for all M01 labs)
From this `labs/` folder:

```bash
# Option A: plain Python (works everywhere)
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install --only-binary=:all: cryptography   # see "Intel Mac" note below
pip install --prefer-binary -r requirements.txt

# Option B: uv
uv venv --python 3.12 && source .venv/bin/activate && uv pip install -r requirements.txt
```

> **Intel Mac / older macOS:** the newest `cryptography` (needed by moto) may have no prebuilt wheel for your platform, and pip then tries to compile it with Rust and Xcode tools and fails. `--only-binary=:all:` makes pip pick the newest version that *has* a wheel.

Each lab also has its own `pyproject.toml` (dependencies, pytest, ruff and mypy settings), so it can become a standalone project later (`uv sync` inside the lab folder).

## Run checks
```bash
./check.sh                 # all three labs: tests + coverage, ruff, format, mypy
cd lab-02-resilient-http-client && pytest -q   # one lab
```

## Labs in this module
- [FastAPI chat service with SSE streaming](lab-01-fastapi-sse-chat/README.md)
- [Resilient HTTP client wrapper](lab-02-resilient-http-client/README.md)
- [Test AWS code with moto](lab-03-moto-aws-testing/README.md)
