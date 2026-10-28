"""Prompts are versioned files under git: prompts/<task>/v1.md, v2.md, ... plus a CURRENT pointer.
A prompt change is a release: a new file, a suite run, a diff, then move CURRENT."""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

VERSION = re.compile(r"^v(\d+)$")


@dataclass(frozen=True)
class Prompt:
    task: str
    version: str
    text: str
    note: str = ""

    @property
    def sha(self) -> str:
        """Ties a report to the exact prompt text, even if someone edits v2.md in place."""
        return hashlib.sha256(self.text.encode()).hexdigest()[:12]


def _split_front_matter(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---\n"):
        return {}, raw.strip()
    _, meta, body = raw.split("---\n", 2)
    data = yaml.safe_load(meta) or {}
    if not isinstance(data, dict):
        raise ValueError("front matter must be a YAML mapping")
    return {str(k): str(v) for k, v in data.items()}, body.strip()


class PromptStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def versions(self, task: str) -> list[str]:
        """v2 before v10: sort by number, not by string."""
        found = [p.stem for p in (self.root / task).glob("v*.md") if VERSION.match(p.stem)]
        return sorted(found, key=lambda v: int(v[1:]))

    def current(self, task: str) -> str:
        version = (self.root / task / "CURRENT").read_text(encoding="utf-8").strip()
        if version not in self.versions(task):
            raise ValueError(f"CURRENT points to {version!r}, which has no prompts/{task}/ file")
        return version

    def load(self, task: str, version: str | None = None) -> Prompt:
        version = version or self.current(task)
        path = self.root / task / f"{version}.md"
        if not path.exists():
            raise FileNotFoundError(f"{path} not found; versions: {self.versions(task)}")
        meta, text = _split_front_matter(path.read_text(encoding="utf-8"))
        return Prompt(task=task, version=version, text=text, note=meta.get("note", ""))
