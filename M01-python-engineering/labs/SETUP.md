# M01 Lab Environment Setup

## Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (`brew install uv`)
- git
- An editor with Python + Ruff extensions

## Python environment
From this `labs/` folder:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Labs in this module
- [FastAPI chat service with SSE streaming](lab-01-fastapi-sse-chat/README.md)
- [Resilient HTTP client wrapper](lab-02-resilient-http-client/README.md)
- [Test AWS code with moto](lab-03-moto-aws-testing/README.md)
