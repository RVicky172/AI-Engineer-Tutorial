import json
from collections.abc import Callable, Iterator
from pathlib import Path

import boto3
import pytest
from moto import mock_aws
from mypy_boto3_s3 import S3Client
from mypy_boto3_secretsmanager import SecretsManagerClient

from config_loader import ConfigLoader

REGION = "us-east-1"
SECRET_ID = "agent/db"
BUCKET = "acme-agent-config"
KEY = "features/prod.json"

DB_SECRET = {"username": "agent", "password": "s3cr3t-Pa55", "host": "db.internal"}
FEATURES = {"model_id": "small-model-v1", "max_tokens": 1024, "enabled_tools": ["get_ticket"]}


@pytest.fixture(autouse=True)
def no_real_aws(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Guarantee no test can ever reach a real AWS account, even on a laptop with an
    admin profile configured: fake keys, and credential/config files that don't exist."""
    for var in ("AWS_PROFILE", "AWS_SESSION_TOKEN", "AWS_SECURITY_TOKEN"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", REGION)
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(tmp_path / "no-credentials"))
    monkeypatch.setenv("AWS_CONFIG_FILE", str(tmp_path / "no-config"))


@pytest.fixture
def aws() -> Iterator[None]:
    # Everything inside is an in-memory fake AWS; state is wiped when the block exits,
    # so every test starts from an empty account.
    with mock_aws():
        yield


@pytest.fixture
def secrets(aws: None) -> SecretsManagerClient:
    return boto3.client("secretsmanager", region_name=REGION)


@pytest.fixture
def s3(aws: None) -> S3Client:
    return boto3.client("s3", region_name=REGION)


@pytest.fixture
def seeded(secrets: SecretsManagerClient, s3: S3Client) -> None:
    secrets.create_secret(Name=SECRET_ID, SecretString=json.dumps(DB_SECRET))
    s3.create_bucket(Bucket=BUCKET)
    s3.put_object(Bucket=BUCKET, Key=KEY, Body=json.dumps(FEATURES).encode())


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def make_loader(
    secrets: SecretsManagerClient, s3: S3Client, clock: FakeClock
) -> Callable[..., ConfigLoader]:
    def factory(**overrides: str) -> ConfigLoader:
        args = {"secret_id": SECRET_ID, "bucket": BUCKET, "key": KEY} | overrides
        return ConfigLoader(
            secrets_client=secrets, s3_client=s3, ttl_seconds=300, clock=clock, **args
        )

    return factory


def count_calls(client: SecretsManagerClient | S3Client, event: str) -> list[str]:
    """Record every API call of one kind using botocore's event system.

    Example event: "before-call.secrets-manager.GetSecretValue". Works with moto, Stubber
    and real AWS alike, because it hooks into botocore itself.
    """
    calls: list[str] = []
    client.meta.events.register(event, lambda **kwargs: calls.append(event))
    return calls
