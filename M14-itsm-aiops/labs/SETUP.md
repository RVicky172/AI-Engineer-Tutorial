# M14 Lab Environment Setup

## Prerequisites
- ServiceNow Personal Developer Instance (wake it up before each session; idle instances hibernate)
- ServiceNow tools from M07 lab-03

## Python environment
From this `labs/` folder:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Labs in this module
- [Seed 20 realistic incidents](lab-01-servicenow-seed-incidents/README.md)
- [Capstone triage agent against ServiceNow](lab-02-capstone-triage-servicenow/README.md)
