"""Lab 02 without an AWS bill: moto plays S3, IAM, STS and S3 Vectors; botocore's Stubber plays
Bedrock and validates every request against the real API model, so a wrong parameter name
fails here, not on a billed call."""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Final

import boto3
import pytest
from botocore.stub import ANY, Stubber
from moto import mock_aws

from kb_lab.cli import PREFIX, main
from kb_lab.infra import Clients, KnowledgeBaseLab, State
from kb_lab.prepare import doc_id_from_uri, metadata_for, prepare
from kb_lab.query import evaluate, group_filter, retrieve, retrieve_and_generate
from ragkit.corpus import Document, load_corpus
from ragkit.golden import load_golden
from tests.paths import LABS

REGION: Final = "ap-south-1"
ACCOUNT = "123456789012"  # moto's default account


@pytest.fixture(scope="session")
def docs() -> list[Document]:
    return load_corpus(LABS / "corpus")


@pytest.fixture
def aws(monkeypatch: pytest.MonkeyPatch) -> Iterator[boto3.Session]:
    for name in ("AWS_PROFILE", "AWS_DEFAULT_PROFILE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    with mock_aws():
        yield boto3.Session(region_name=REGION)


def test_prepare_strips_front_matter_and_writes_sidecars(
    docs: list[Document], tmp_path: Path
) -> None:
    files = prepare(docs, tmp_path / "up")
    assert len(files) == 2 * len(docs)
    body = (tmp_path / "up" / "kb-teams-audio.md").read_text(encoding="utf-8")
    assert not body.startswith("---") and "allowed_groups" not in body
    sidecar = json.loads((tmp_path / "up" / "kb-teams-audio.md.metadata.json").read_text())
    assert sidecar["metadataAttributes"]["allowed_groups"] == ["all-staff"]
    assert (tmp_path / "up" / "travel-expense-policy.pdf").read_bytes().startswith(b"%PDF")
    prepare(docs[:1], tmp_path / "up")  # re-running replaces, not appends
    assert len(list((tmp_path / "up").iterdir())) == 2


def test_metadata_carries_status_so_superseded_docs_can_be_filtered(
    docs: list[Document],
) -> None:
    old = next(d for d in docs if d.doc_id == "pol-incident-severity-2024")
    assert metadata_for(old)["metadataAttributes"]["status"] == "superseded"  # type: ignore[index]
    assert doc_id_from_uri("s3://b/corpus/vendor-sla-summary.pdf") == "vendor-sla-summary"


def test_group_filter_matches_lab_03s_rule() -> None:
    one = {"listContains": {"key": "allowed_groups", "value": "all-staff"}}
    assert group_filter(["all-staff"]) == one
    assert group_filter(["it-ops", "all-staff"]) == {
        "orAll": [one, {"listContains": {"key": "allowed_groups", "value": "it-ops"}}]
    }
    with pytest.raises(ValueError, match="no groups"):
        group_filter([])


def stubbed(session: Any, service: str) -> tuple[Any, Stubber]:
    client = session.client(service)
    return client, Stubber(client)


def test_up_ingest_down_leaves_nothing_behind(
    aws: boto3.Session, docs: list[Document], tmp_path: Path
) -> None:
    agent, stub = stubbed(aws, "bedrock-agent")
    clients = Clients(aws.client("s3"), aws.client("s3vectors"), aws.client("iam"), agent)
    state_path = tmp_path / "state.json"
    sleeps: list[float] = []
    lab = KnowledgeBaseLab(clients, State(PREFIX, REGION, ACCOUNT), state_path, sleep=sleeps.append)

    files = prepare(docs, tmp_path / "up")
    lab.create_bucket(files, tmp_path / "up")
    lab.create_vector_store()
    lab.create_role()
    assert State.load(state_path).role_arn.endswith(f"role/{PREFIX}-kb-role")

    kb = {
        "knowledgeBaseId": "KB12345678",
        "name": f"{PREFIX}-kb",
        "roleArn": "r",
        "knowledgeBaseArn": "arn",
        "status": "CREATING",
        "createdAt": "2026-10-28",
        "updatedAt": "2026-10-28",
        "knowledgeBaseConfiguration": {"type": "VECTOR"},
    }
    ds = {
        "knowledgeBaseId": "KB12345678",
        "dataSourceId": "DS12345678",
        "name": "d",
        "status": "AVAILABLE",
        "createdAt": "2026-10-28",
        "updatedAt": "2026-10-28",
        "dataSourceConfiguration": {"type": "S3"},
    }
    job = {
        "knowledgeBaseId": "KB12345678",
        "dataSourceId": "DS12345678",
        "ingestionJobId": "J123456789",
        "startedAt": "2026-10-28",
        "updatedAt": "2026-10-28",
    }
    # first attempt: the new role hasn't propagated yet
    stub.add_client_error(
        "create_knowledge_base",
        "ValidationException",
        "The knowledge base storage configuration provided is invalid... role",
    )
    stub.add_response(
        "create_knowledge_base",
        {"knowledgeBase": kb},
        {
            "name": f"{PREFIX}-kb",
            "roleArn": ANY,
            "knowledgeBaseConfiguration": ANY,
            "storageConfiguration": {
                "type": "S3_VECTORS",
                "s3VectorsConfiguration": {"indexArn": ANY},
            },
        },
    )
    stub.add_response(
        "create_data_source",
        {"dataSource": ds},
        {
            "knowledgeBaseId": "KB12345678",
            "name": ANY,
            "dataSourceConfiguration": ANY,
            "vectorIngestionConfiguration": {
                "chunkingConfiguration": {
                    "chunkingStrategy": "FIXED_SIZE",
                    "fixedSizeChunkingConfiguration": {"maxTokens": 256, "overlapPercentage": 12},
                }
            },
        },
    )
    stub.add_response("start_ingestion_job", {"ingestionJob": {**job, "status": "IN_PROGRESS"}})
    stub.add_response(
        "get_ingestion_job",
        {
            "ingestionJob": {
                **job,
                "status": "COMPLETE",
                "statistics": {
                    "numberOfDocumentsScanned": 77,
                    "numberOfNewDocumentsIndexed": 77,
                    "numberOfDocumentsFailed": 0,
                },
            }
        },
    )
    stub.add_response(
        "delete_data_source",
        {"knowledgeBaseId": "KB12345678", "dataSourceId": "DS12345678", "status": "DELETING"},
    )
    stub.add_response(
        "delete_knowledge_base", {"knowledgeBaseId": "KB12345678", "status": "DELETING"}
    )
    stub.add_response("list_knowledge_bases", {"knowledgeBaseSummaries": []})
    # second `down`: everything is already gone, and that must not be an error
    stub.add_client_error("delete_data_source", "ResourceNotFoundException")
    stub.add_client_error("delete_knowledge_base", "ResourceNotFoundException")

    with stub:
        lab.create_knowledge_base()
        result = lab.ingest(poll_seconds=15)
        assert result["status"] == "COMPLETE"
        assert result["statistics"]["numberOfDocumentsFailed"] == 0
        assert sleeps == [10, 15]  # one role-propagation retry, one poll
        assert aws.client("s3").list_objects_v2(Bucket=lab.state.bucket)["KeyCount"] == len(files)

        lab.down()
        assert lab.remaining() == []
        lab.down()
        stub.assert_no_pending_responses()


def test_role_policy_is_least_privilege(tmp_path: Path) -> None:
    state = State(PREFIX, REGION, ACCOUNT, bucket="b", index_arn="arn:idx")
    policy = KnowledgeBaseLab(Clients(None, None, None, None), state, tmp_path / "s").policy()
    resources = [s["Resource"] for s in policy["Statement"]]
    actions = json.dumps([s["Action"] for s in policy["Statement"]])
    assert "*" not in resources  # no account-wide resource
    assert ":*" not in actions  # no wildcard actions like s3:*
    assert "arn:aws:s3:::b/corpus/*" in resources and "arn:idx" in resources  # scoped wildcard


def test_ingestion_times_out_instead_of_waiting_forever(aws: boto3.Session, tmp_path: Path) -> None:
    agent, stub = stubbed(aws, "bedrock-agent")
    state = State(PREFIX, REGION, ACCOUNT, kb_id="KB00000001", data_source_id="DS12345678")
    lab = KnowledgeBaseLab(
        Clients(None, None, None, agent), state, tmp_path / "s", sleep=lambda s: None
    )
    job = {
        "knowledgeBaseId": "KB00000001",
        "dataSourceId": "DS12345678",
        "ingestionJobId": "J000000001",
        "status": "IN_PROGRESS",
        "startedAt": "2026-10-28",
        "updatedAt": "2026-10-28",
    }
    stub.add_response("start_ingestion_job", {"ingestionJob": job})
    stub.add_response("get_ingestion_job", {"ingestionJob": job})
    with stub, pytest.raises(TimeoutError, match="still IN_PROGRESS"):
        lab.ingest(poll_seconds=10, timeout_seconds=10)


def retrieval_result(doc_id: str, text: str, score: float) -> dict[str, Any]:
    return {
        "content": {"text": text},
        "score": score,
        "location": {"type": "S3", "s3Location": {"uri": f"s3://b/corpus/{doc_id}.md"}},
        "metadata": {"doc_id": doc_id},
    }


def test_retrieve_sends_the_acl_filter_and_maps_doc_ids(aws: boto3.Session) -> None:
    runtime, stub = stubbed(aws, "bedrock-agent-runtime")
    stub.add_response(
        "retrieve",
        {"retrievalResults": [retrieval_result("kb-printer-error-codes", "E-340: fuser", 0.8)]},
        {
            "knowledgeBaseId": "KB00000001",
            "retrievalQuery": {"text": "E-340?"},
            "retrievalConfiguration": {
                "vectorSearchConfiguration": {
                    "numberOfResults": 10,
                    "filter": {"listContains": {"key": "allowed_groups", "value": "all-staff"}},
                }
            },
        },
    )
    with stub:
        hits = retrieve(runtime, "KB00000001", "E-340?", groups=["all-staff"])
    assert [(h.doc_id, h.score) for h in hits] == [("kb-printer-error-codes", 0.8)]


def test_evaluate_scores_the_kb_like_pgvector(docs: list[Document]) -> None:
    questions = load_golden(LABS / "golden.yaml", {d.doc_id for d in docs})[:2]

    class Runtime:
        def __init__(self) -> None:
            self.filters: list[Any] = []

        def retrieve(self, **kwargs: Any) -> dict[str, Any]:
            self.filters.append(
                kwargs["retrievalConfiguration"]["vectorSearchConfiguration"].get("filter")
            )
            q = next(q for q in questions if q.question == kwargs["retrievalQuery"]["text"])
            doc = next(d for d in docs if d.doc_id == q.relevant[0])
            return {"retrievalResults": [retrieval_result(doc.doc_id, doc.text, 0.9)]}

    runtime = Runtime()
    plain = evaluate(runtime, "KB00000001", questions, clock=iter(range(100)).__next__)
    assert (plain.recall_at_5, plain.evidence_at_5, plain.mrr) == (1.0, 1.0, 1.0)
    as_askers = evaluate(runtime, "KB00000001", questions, as_askers=True)
    assert as_askers.name == "knowledge base (as askers)"
    assert runtime.filters[:2] == [None, None] and all(runtime.filters[2:])


def test_retrieve_and_generate_returns_answer_and_cited_docs(aws: boto3.Session) -> None:
    runtime, stub = stubbed(aws, "bedrock-agent-runtime")
    ref = {
        "content": {"text": "x"},
        "location": {"type": "S3", "s3Location": {"uri": "s3://b/corpus/kb-reset-sso-password.md"}},
    }
    stub.add_response(
        "retrieve_and_generate",
        {
            "sessionId": "session-1",
            "output": {"text": "Use the reset page."},
            "citations": [{"retrievedReferences": [ref, ref]}],
        },
    )
    with stub:
        text, cited = retrieve_and_generate(
            runtime, "KB00000001", "arn:model", "Reset?", groups=["a", "b"]
        )
    assert text == "Use the reset page." and cited == ["kb-reset-sso-password"]


def test_cli_prepare_and_the_billing_guard(
    aws: boto3.Session, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["prepare", "--out", str(tmp_path / "up")]) == 0
    state = ["--region", REGION, "--state", str(tmp_path / "s.json")]
    assert main([*state, "up"], session_factory=lambda r: aws) == 2  # no --yes: nothing created
    out = capsys.readouterr().out
    assert "BILLABLE" in out and "--yes" in out
    assert aws.client("s3").list_buckets()["Buckets"] == []
    assert main([*state, "eval"], session_factory=lambda r: aws) == 2  # no KB yet


def test_cli_status_and_down_report_what_remains(
    aws: boto3.Session, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    moto: Any = aws  # boto3-stubs only types .client() with literal service names

    class Session:
        region_name = REGION

        def client(self, name: str) -> Any:
            if name != "bedrock-agent":
                return moto.client(name)
            agent = moto.client(name)
            stub = Stubber(agent)
            stub.add_response("list_knowledge_bases", {"knowledgeBaseSummaries": []})
            stub.activate()
            return agent

    aws.client("s3").create_bucket(
        Bucket=f"{PREFIX}-docs-leftover", CreateBucketConfiguration={"LocationConstraint": REGION}
    )
    args = ["--region", REGION, "--state", str(tmp_path / "s.json")]
    assert main([*args, "status"], session_factory=lambda r: Session()) == 0
    assert f"s3 bucket {PREFIX}-docs-leftover" in capsys.readouterr().out
    assert main([*args, "down"], session_factory=lambda r: Session()) == 1  # not in state: kept


class StubSession:
    """moto for S3/IAM/STS/S3 Vectors, a pre-loaded Stubber for each Bedrock client."""

    region_name = REGION

    def __init__(self, aws: Any, scripts: dict[str, list[tuple[str, Any]]]) -> None:
        self.aws, self.scripts = aws, scripts

    def client(self, name: str) -> Any:
        client = self.aws.client(name)
        if name in self.scripts:
            stub = Stubber(client)
            for operation, response in self.scripts[name]:
                stub.add_response(operation, response)
            stub.activate()
        return client


def test_cli_up_eval_ask_down(
    aws: boto3.Session, docs: list[Document], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    kb = {
        "knowledgeBaseId": "KB12345678",
        "name": "kb",
        "roleArn": "r",
        "knowledgeBaseArn": "a",
        "status": "ACTIVE",
        "createdAt": "2026-10-28",
        "updatedAt": "2026-10-28",
        "knowledgeBaseConfiguration": {"type": "VECTOR"},
    }
    ds = {
        "knowledgeBaseId": "KB12345678",
        "dataSourceId": "DS12345678",
        "name": "d",
        "status": "AVAILABLE",
        "createdAt": "2026-10-28",
        "updatedAt": "2026-10-28",
        "dataSourceConfiguration": {"type": "S3"},
    }
    job = {
        "knowledgeBaseId": "KB12345678",
        "dataSourceId": "DS12345678",
        "ingestionJobId": "J123456789",
        "startedAt": "2026-10-28",
        "updatedAt": "2026-10-28",
        "status": "FAILED",
        "failureReasons": ["1 document failed: unsupported format"],
    }
    state = ["--region", REGION, "--state", str(tmp_path / "s.json")]
    session = StubSession(
        aws,
        {
            "bedrock-agent": [
                ("create_knowledge_base", {"knowledgeBase": kb}),
                ("create_data_source", {"dataSource": ds}),
                ("start_ingestion_job", {"ingestionJob": job}),
            ]
        },
    )
    assert main([*state, "up", "--yes"], session_factory=lambda r: session) == 1  # job FAILED
    assert "failure: 1 document failed" in capsys.readouterr().out
    assert State.load(tmp_path / "s.json").kb_id == "KB12345678"

    hit = retrieval_result("kb-printer-error-codes", "E-340: fuser error", 0.8)
    ref = {
        "content": {"text": "x"},
        "location": {
            "type": "S3",
            "s3Location": {"uri": "s3://b/corpus/kb-printer-error-codes.md"},
        },
    }
    # every CLI run builds its own clients, so each run gets its own script
    retrieves = [("retrieve", {"retrievalResults": [hit]})] * 50  # 25 questions, twice
    evaluation = StubSession(aws, {"bedrock-agent-runtime": retrieves})
    assert main([*state, "eval"], session_factory=lambda r: evaluation) == 0
    assert "knowledge base (as askers)" in capsys.readouterr().out
    rag = {
        "sessionId": "session-1",
        "output": {"text": "Fuser."},
        "citations": [{"retrievedReferences": [ref]}],
    }
    asking = StubSession(aws, {"bedrock-agent-runtime": [("retrieve_and_generate", rag)]})
    ask = [*state, "ask", "E-340?", "--model-arn", "arn:m", "--groups", "all-staff"]
    assert main(ask, session_factory=lambda r: asking) == 0
    assert "Cited: kb-printer-error-codes" in capsys.readouterr().out

    session = StubSession(
        aws,
        {
            "bedrock-agent": [
                (
                    "delete_data_source",
                    {
                        "knowledgeBaseId": "KB12345678",
                        "dataSourceId": "DS12345678",
                        "status": "DELETING",
                    },
                ),
                ("delete_knowledge_base", {"knowledgeBaseId": "KB12345678", "status": "DELETING"}),
                ("list_knowledge_bases", {"knowledgeBaseSummaries": []}),
            ]
        },
    )
    assert main([*state, "down"], session_factory=lambda r: session) == 0
    assert "none" in capsys.readouterr().out
    assert not (tmp_path / "s.json").exists()
