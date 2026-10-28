"""Create and delete everything Lab 02 needs, and record it so nothing is left running.

Vector store: Amazon S3 Vectors. It bills for storage and queries, not per hour, so a lab KB
left running overnight costs cents. The alternative many tutorials use, OpenSearch Serverless,
bills per OCU-hour while the collection exists, whether you query it or not. Check current
prices on the pricing pages before choosing; they change.

Every resource is written to a state file as soon as it exists, so `down` can delete it even
if `up` crashed half way. `remaining()` then lists anything with the lab prefix that survived."""

import json
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from botocore.exceptions import ClientError

EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
DIMENSIONS = 1024
NOT_FOUND = {"ResourceNotFoundException", "NoSuchBucket", "NoSuchEntity", "NotFoundException"}


@dataclass
class State:
    prefix: str
    region: str
    account: str
    bucket: str = ""
    vector_bucket: str = ""
    index_arn: str = ""
    role_name: str = ""
    role_arn: str = ""
    kb_id: str = ""
    data_source_id: str = ""
    ingestion: dict[str, Any] = field(default_factory=dict)

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "State":
        return cls(**json.loads(path.read_text(encoding="utf-8")))


@dataclass
class Clients:
    s3: Any
    s3vectors: Any
    iam: Any
    agent: Any  # bedrock-agent (control plane)

    @classmethod
    def from_session(cls, session: Any) -> "Clients":
        return cls(
            s3=session.client("s3"),
            s3vectors=session.client("s3vectors"),
            iam=session.client("iam"),
            agent=session.client("bedrock-agent"),
        )


def _ignore_missing(call: Callable[[], Any]) -> None:
    """Teardown must be re-runnable: deleting what is already gone is success."""
    try:
        call()
    except ClientError as exc:
        if exc.response["Error"]["Code"] not in NOT_FOUND:
            raise


class KnowledgeBaseLab:
    def __init__(
        self,
        clients: Clients,
        state: State,
        state_path: Path,
        *,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.c, self.state, self.state_path, self.sleep = clients, state, state_path, sleep

    def _save(self) -> None:
        self.state.save(self.state_path)

    # ---- create -----------------------------------------------------------------------------

    def create_bucket(self, files: list[Path], root: Path) -> None:
        s = self.state
        s.bucket = f"{s.prefix}-docs-{s.account}"
        kwargs: dict[str, Any] = {"Bucket": s.bucket}
        if s.region != "us-east-1":  # us-east-1 rejects an explicit LocationConstraint
            kwargs["CreateBucketConfiguration"] = {"LocationConstraint": s.region}
        self.c.s3.create_bucket(**kwargs)
        self._save()
        self.c.s3.put_public_access_block(
            Bucket=s.bucket,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        )
        for f in files:
            self.c.s3.upload_file(str(f), s.bucket, f"corpus/{f.relative_to(root).as_posix()}")

    def create_vector_store(self) -> None:
        s = self.state
        s.vector_bucket = f"{s.prefix}-vectors-{s.account}"
        self.c.s3vectors.create_vector_bucket(vectorBucketName=s.vector_bucket)
        self._save()
        response = self.c.s3vectors.create_index(
            vectorBucketName=s.vector_bucket,
            indexName="chunks",
            dataType="float32",
            dimension=DIMENSIONS,
            distanceMetric="cosine",
            # The KB stores each chunk's text and its metadata JSON as vector metadata. Filterable
            # metadata has a small size limit, so these two must be non-filterable or ingestion
            # of longer chunks fails. (Check the current KB + S3 Vectors docs for the limits.)
            metadataConfiguration={
                "nonFilterableMetadataKeys": ["AMAZON_BEDROCK_TEXT", "AMAZON_BEDROCK_METADATA"]
            },
        )
        s.index_arn = response.get("indexArn") or (
            f"arn:aws:s3vectors:{s.region}:{s.account}:bucket/{s.vector_bucket}/index/chunks"
        )
        self._save()

    def create_role(self) -> None:
        s = self.state
        s.role_name = f"{s.prefix}-kb-role"
        trust = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "bedrock.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                    # confused-deputy protection: only KBs in this account may use the role
                    "Condition": {"StringEquals": {"aws:SourceAccount": s.account}},
                }
            ],
        }
        role = self.c.iam.create_role(
            RoleName=s.role_name, AssumeRolePolicyDocument=json.dumps(trust)
        )
        s.role_arn = role["Role"]["Arn"]
        self._save()
        self.c.iam.put_role_policy(
            RoleName=s.role_name, PolicyName="kb-access", PolicyDocument=json.dumps(self.policy())
        )

    def policy(self) -> dict[str, Any]:
        """Least privilege: one embedding model, one bucket prefix, one vector index."""
        s = self.state
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "bedrock:InvokeModel",
                    "Resource": f"arn:aws:bedrock:{s.region}::foundation-model/{EMBEDDING_MODEL}",
                },
                {
                    "Effect": "Allow",
                    "Action": "s3:ListBucket",
                    "Resource": f"arn:aws:s3:::{s.bucket}",
                    "Condition": {"StringLike": {"s3:prefix": ["corpus/*"]}},
                },
                {
                    "Effect": "Allow",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{s.bucket}/corpus/*",
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3vectors:PutVectors",
                        "s3vectors:GetVectors",
                        "s3vectors:DeleteVectors",
                        "s3vectors:QueryVectors",
                        "s3vectors:GetIndex",
                    ],
                    "Resource": s.index_arn,
                },
            ],
        }

    def create_knowledge_base(self, *, chunk_tokens: int = 256, overlap_pct: int = 12) -> None:
        """Fixed-size chunking at 256 tokens / 12% overlap: the same as the pgvector build, so
        the comparison is about the platform, not the chunker. (Stretch: try HIERARCHICAL or
        SEMANTIC here.)"""
        s = self.state
        model_arn = f"arn:aws:bedrock:{s.region}::foundation-model/{EMBEDDING_MODEL}"
        kb_config = {
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": model_arn,
                "embeddingModelConfiguration": {
                    "bedrockEmbeddingModelConfiguration": {"dimensions": DIMENSIONS}
                },
            },
        }
        storage = {"type": "S3_VECTORS", "s3VectorsConfiguration": {"indexArn": s.index_arn}}
        for attempt in range(6):
            try:
                kb = self.c.agent.create_knowledge_base(
                    name=f"{s.prefix}-kb",
                    roleArn=s.role_arn,
                    knowledgeBaseConfiguration=kb_config,
                    storageConfiguration=storage,
                )
                break
            except ClientError as exc:
                # A new IAM role takes seconds to propagate; Bedrock reports that as a
                # ValidationException about the role. Anything else is a real error.
                retryable = exc.response["Error"]["Code"] == "ValidationException" and (
                    "role" in str(exc).lower()
                )
                if not retryable or attempt == 5:
                    raise
                self.sleep(10)
        s.kb_id = kb["knowledgeBase"]["knowledgeBaseId"]
        self._save()
        ds = self.c.agent.create_data_source(
            knowledgeBaseId=s.kb_id,
            name=f"{s.prefix}-corpus",
            dataSourceConfiguration={
                "type": "S3",
                "s3Configuration": {
                    "bucketArn": f"arn:aws:s3:::{s.bucket}",
                    "inclusionPrefixes": ["corpus/"],
                },
            },
            vectorIngestionConfiguration={
                "chunkingConfiguration": {
                    "chunkingStrategy": "FIXED_SIZE",
                    "fixedSizeChunkingConfiguration": {
                        "maxTokens": chunk_tokens,
                        "overlapPercentage": overlap_pct,
                    },
                }
            },
        )
        s.data_source_id = ds["dataSource"]["dataSourceId"]
        self._save()

    def ingest(self, *, poll_seconds: float = 15, timeout_seconds: float = 1800) -> dict[str, Any]:
        """Start a sync and wait. Read the statistics and failureReasons: a KB that 'succeeded'
        can still have skipped documents."""
        s = self.state
        job = self.c.agent.start_ingestion_job(
            knowledgeBaseId=s.kb_id, dataSourceId=s.data_source_id
        )["ingestionJob"]
        waited = 0.0
        while job["status"] not in ("COMPLETE", "FAILED", "STOPPED"):
            if waited >= timeout_seconds:
                raise TimeoutError(f"ingestion job {job['ingestionJobId']} still {job['status']}")
            self.sleep(poll_seconds)
            waited += poll_seconds
            job = self.c.agent.get_ingestion_job(
                knowledgeBaseId=s.kb_id,
                dataSourceId=s.data_source_id,
                ingestionJobId=job["ingestionJobId"],
            )["ingestionJob"]
        s.ingestion = {
            "status": job["status"],
            "statistics": job.get("statistics", {}),
            "failureReasons": job.get("failureReasons", []),
            "seconds_waited": waited,
        }
        self._save()
        return s.ingestion

    # ---- delete -----------------------------------------------------------------------------

    def down(self) -> None:
        """Reverse order of creation. Each step tolerates 'already gone'."""
        s = self.state
        if s.kb_id and s.data_source_id:
            _ignore_missing(
                lambda: self.c.agent.delete_data_source(
                    knowledgeBaseId=s.kb_id, dataSourceId=s.data_source_id
                )
            )
        if s.kb_id:
            _ignore_missing(lambda: self.c.agent.delete_knowledge_base(knowledgeBaseId=s.kb_id))
        if s.vector_bucket:
            _ignore_missing(
                lambda: self.c.s3vectors.delete_index(
                    vectorBucketName=s.vector_bucket, indexName="chunks"
                )
            )
            _ignore_missing(
                lambda: self.c.s3vectors.delete_vector_bucket(vectorBucketName=s.vector_bucket)
            )
        if s.bucket:
            _ignore_missing(lambda: self._empty_and_delete_bucket(s.bucket))
        if s.role_name:
            _ignore_missing(
                lambda: self.c.iam.delete_role_policy(RoleName=s.role_name, PolicyName="kb-access")
            )
            _ignore_missing(lambda: self.c.iam.delete_role(RoleName=s.role_name))

    def _empty_and_delete_bucket(self, bucket: str) -> None:
        paginator = self.c.s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket):
            keys = [{"Key": o["Key"]} for o in page.get("Contents", [])]
            if keys:
                self.c.s3.delete_objects(Bucket=bucket, Delete={"Objects": keys})
        self.c.s3.delete_bucket(Bucket=bucket)

    def remaining(self) -> list[str]:
        """Everything with the lab prefix that still exists: the evidence for 'all deleted'."""
        p = self.state.prefix
        left = [
            f"s3 bucket {b['Name']}"
            for b in self.c.s3.list_buckets().get("Buckets", [])
            if b["Name"].startswith(p)
        ]
        left += [
            f"vector bucket {b['vectorBucketName']}"
            for b in self.c.s3vectors.list_vector_buckets().get("vectorBuckets", [])
            if b["vectorBucketName"].startswith(p)
        ]
        left += [
            f"knowledge base {k['name']} ({k['knowledgeBaseId']}, {k['status']})"
            for k in self.c.agent.list_knowledge_bases().get("knowledgeBaseSummaries", [])
            if k["name"].startswith(p)
        ]
        left += [
            f"iam role {r['RoleName']}"
            for r in self.c.iam.list_roles().get("Roles", [])
            if r["RoleName"].startswith(p)
        ]
        return left
