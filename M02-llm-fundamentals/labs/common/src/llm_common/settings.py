import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

Provider = Literal["anthropic", "bedrock"]
Effort = Literal["low", "medium", "high", "xhigh", "max"]

DEFAULT_MODEL = "claude-opus-5-5"
# labs/.env: one file configures every M02 lab.
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


@dataclass(frozen=True)
class Settings:
    """Which provider and model the labs call. Nothing here is a secret: credentials stay with
    the SDK's own lookup (ANTHROPIC_API_KEY / `ant auth login`, or the AWS credential chain)."""

    provider: Provider = "anthropic"
    model: str = DEFAULT_MODEL
    aws_region: str | None = None
    aws_profile: str | None = None

    @classmethod
    def from_env(cls, env_file: Path | None = ENV_FILE) -> "Settings":
        if env_file is not None and env_file.exists():
            # override=False: a variable exported in the shell wins over the file.
            load_dotenv(env_file, override=False)
        raw = os.environ.get("LLM_PROVIDER") or "anthropic"
        if raw not in ("anthropic", "bedrock"):
            raise ValueError(f"LLM_PROVIDER must be 'anthropic' or 'bedrock', got {raw!r}")
        return cls(
            provider="bedrock" if raw == "bedrock" else "anthropic",
            model=os.environ.get("LLM_MODEL") or DEFAULT_MODEL,
            aws_region=os.environ.get("AWS_REGION") or None,
            aws_profile=os.environ.get("AWS_PROFILE") or None,
        )

    @property
    def api_model_id(self) -> str:
        """The ID to send. Bedrock IDs carry an `anthropic.` prefix; reports use the bare ID."""
        if self.provider == "bedrock" and "anthropic." not in self.model:
            return f"anthropic.{self.model}"
        return self.model
