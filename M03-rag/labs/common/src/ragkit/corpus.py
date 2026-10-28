"""Load the corpus: Markdown with YAML front matter, and PDFs with a `<name>.pdf.meta.yaml` sidecar
(the same idea as Bedrock Knowledge Bases' `.metadata.json` files)."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pypdf import PdfReader


@dataclass(frozen=True)
class Document:
    doc_id: str  # file name without extension: stable, human-readable, used in citations
    title: str
    text: str
    allowed_groups: tuple[str, ...]
    metadata: dict[str, str]  # type, service, updated, source format
    path: Path


def _parse_yaml(text: str, path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:  # name the file: one bad doc in 10,000 must be findable
        raise ValueError(f"{path.name}: invalid metadata YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: metadata must be a mapping")
    return data


def _meta(raw: dict[str, Any], path: Path) -> tuple[str, tuple[str, ...], dict[str, str]]:
    missing = {"title", "allowed_groups"} - raw.keys()
    if missing:
        raise ValueError(f"{path.name}: metadata is missing {sorted(missing)}")
    groups = raw["allowed_groups"]
    if not isinstance(groups, list) or not groups:
        raise ValueError(f"{path.name}: allowed_groups must be a non-empty list")
    extra = {k: str(v) for k, v in raw.items() if k not in ("title", "allowed_groups")}
    return str(raw["title"]), tuple(str(g) for g in groups), extra


def load_markdown(path: Path) -> Document:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        raise ValueError(f"{path.name}: no front matter")
    _, front, body = raw.split("---\n", 2)
    title, groups, meta = _meta(_parse_yaml(front, path), path)
    return Document(path.stem, title, body.strip(), groups, {**meta, "format": "md"}, path)


def load_pdf(path: Path) -> Document:
    sidecar = path.with_name(path.name + ".meta.yaml")
    if not sidecar.exists():
        raise ValueError(f"{path.name}: no {sidecar.name} sidecar")
    title, groups, meta = _meta(_parse_yaml(sidecar.read_text(encoding="utf-8"), path), path)
    text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    return Document(path.stem, title, text.strip(), groups, {**meta, "format": "pdf"}, path)


def load_corpus(root: Path) -> list[Document]:
    docs = [load_markdown(p) for p in sorted(root.glob("*.md"))]
    docs += [load_pdf(p) for p in sorted(root.glob("*.pdf"))]
    ids = [d.doc_id for d in docs]
    if dupes := sorted({i for i in ids if ids.count(i) > 1}):
        raise ValueError(f"duplicate doc ids: {dupes}")
    return docs
