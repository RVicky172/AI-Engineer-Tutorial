# M02 Lab Environment Setup

## Prerequisites
- Completed M01 setup (Python 3.12+, git)
- Access to Claude through **one** of:
  - the **Claude API**: `ant auth login` once, or an `ANTHROPIC_API_KEY`
  - **Amazon Bedrock**: model access enabled in the console, and AWS credentials for your **sandbox** account
- A spend limit before you call any model: a Console spend limit (Claude API) or an AWS Budget alarm, e.g. $20/month (Bedrock)

## Python environment (one shared venv for all M02 labs)
From this `labs/` folder:

```bash
# Option A: plain Python
python3.12 -m venv .venv
source .venv/bin/activate          # Windows Git Bash: source .venv/Scripts/activate
pip install --upgrade pip
pip install -r requirements.txt

# Option B: uv
uv venv --python 3.12 && source .venv/bin/activate && uv pip install -r requirements.txt
```

`requirements.txt` installs the shared helper package `common/` (`llm_common`) and all three labs as editable packages, so `python -m extraction`, `python -m tool_design` and `python -m regression` work from anywhere.

## Configure the model
```bash
cp .env.example .env     # .env is git-ignored
```
| Variable | Meaning |
|---|---|
| `LLM_PROVIDER` | `anthropic` (default) or `bedrock` |
| `LLM_MODEL` | default `claude-opus-5-5`; `claude-haiku-5-5` is much cheaper for iterating |
| `AWS_PROFILE`, `AWS_REGION` | Bedrock only |

The labs never read secrets from `.env` themselves: the Anthropic SDK finds `ANTHROPIC_API_KEY` or your `ant auth login` profile, and the Bedrock client uses the AWS credential chain. Both providers serve the same Messages API, so every lab runs unchanged on either.

## Two kinds of checks
```bash
./check.sh     # offline: unit tests + coverage, ruff, format, mypy for every lab. No model calls, $0.
```
Every lab's tests use a scripted fake model (`llm_common.fake.FakeMessages`) and a real SDK client on an in-memory transport, so they are fast, deterministic and free. **Live runs** call the real model and cost money; each lab's `NOTES.md` lists its live commands. Start every live run with `--limit 3` (or `--repeats 1`) as a smoke test.

| Lab | Live command | Calls (full run) |
|---|---|---|
| 01 | `python -m extraction` | 90 (30 emails x 3 techniques) |
| 02 | `python -m tool_design select` / `recover` | 50 / ~30 |
| 03 | `pytest lab-03-prompt-regression-suite/evals/` | 60 per prompt version (20 cases x 3) |

## AWS checklist (Bedrock only)
- [ ] `aws sts get-caller-identity` returns your **sandbox** account
- [ ] Region set, and the Claude model you chose is enabled there
- [ ] AWS Budget alarm exists

## Labs in this module
- [One extraction task, three techniques](lab-01-extraction-three-ways/README.md)
- [Tool design for an IT-support agent](lab-02-tool-design-it-support/README.md)
- [Prompt regression suite](lab-03-prompt-regression-suite/README.md)
