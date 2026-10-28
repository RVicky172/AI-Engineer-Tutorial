"""Turn the corpus into what a Knowledge Base ingests: one file per document plus a
`<file>.metadata.json` sidecar. Metadata becomes filterable at query time, which is how the KB
gets the same document-level access control as Lab 03."""

import json
import shutil
from pathlib import Path

from ragkit.corpus import Document


def metadata_for(doc: Document) -> dict[str, object]:
    """The sidecar format: {"metadataAttributes": {key: value}}. Lists of strings become
    STRING_LIST attributes, which the `listContains` filter works on."""
    attrs: dict[str, object] = {
        "doc_id": doc.doc_id,  # also in the S3 key, but a filterable attribute is handier
        "allowed_groups": list(doc.allowed_groups),
        "title": doc.title,
    }
    for key in ("type", "service", "status", "updated"):
        if key in doc.metadata:
            attrs[key] = doc.metadata[key]
    return {"metadataAttributes": attrs}


def prepare(docs: list[Document], out: Path) -> list[Path]:
    """Markdown is written without its front matter (the KB would otherwise chunk the YAML as
    text); PDFs are copied as they are. Returns every file written, sidecars included."""
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    written = []
    for doc in docs:
        if doc.metadata["format"] == "pdf":
            target = out / doc.path.name
            shutil.copyfile(doc.path, target)
        else:
            target = out / f"{doc.doc_id}.md"
            target.write_text(doc.text + "\n", encoding="utf-8")
        sidecar = target.with_name(target.name + ".metadata.json")
        sidecar.write_text(json.dumps(metadata_for(doc), indent=2), encoding="utf-8")
        written += [target, sidecar]
    return written


def doc_id_from_uri(uri: str) -> str:
    """s3://bucket/corpus/kb-teams-audio.md -> kb-teams-audio (same ids as the golden set)."""
    name = uri.rsplit("/", 1)[-1]
    return name.rsplit(".", 1)[0]
