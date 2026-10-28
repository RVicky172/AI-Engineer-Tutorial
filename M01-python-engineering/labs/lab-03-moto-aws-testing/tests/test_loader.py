import json
import traceback
from collections.abc import Callable

import boto3
import pytest
from botocore.stub import Stubber
from mypy_boto3_s3 import S3Client
from mypy_boto3_secretsmanager import SecretsManagerClient

from config_loader import ConfigError, ConfigLoader
from tests.conftest import (
    BUCKET,
    DB_SECRET,
    KEY,
    REGION,
    SECRET_ID,
    FakeClock,
    count_calls,
)

pytestmark = pytest.mark.usefixtures("seeded")


def test_loads_typed_config(make_loader: Callable[..., ConfigLoader]) -> None:
    config = make_loader().load()

    assert config.db.username == "agent"
    assert config.db.password.get_secret_value() == DB_SECRET["password"]
    assert config.db.port == 5432  # default applied
    assert config.features.model_id == "small-model-v1"
    assert config.features.enabled_tools == ["get_ticket"]


def test_password_is_masked_when_printed_or_logged(
    make_loader: Callable[..., ConfigLoader],
) -> None:
    config = make_loader().load()
    for rendering in (repr(config), str(config), str(config.db), config.db.model_dump_json()):
        assert DB_SECRET["password"] not in rendering


def test_fetches_once_within_ttl(
    make_loader: Callable[..., ConfigLoader],
    secrets: SecretsManagerClient,
    s3: S3Client,
    clock: FakeClock,
) -> None:
    secret_calls = count_calls(secrets, "before-call.secrets-manager.GetSecretValue")
    object_calls = count_calls(s3, "before-call.s3.GetObject")
    loader = make_loader()

    for _ in range(5):
        loader.load()
        clock.now += 50  # 4 x 50s = 200s, still inside the 300s TTL

    assert len(secret_calls) == 1
    assert len(object_calls) == 1


def test_refetches_after_ttl_and_after_invalidate(
    make_loader: Callable[..., ConfigLoader], secrets: SecretsManagerClient, clock: FakeClock
) -> None:
    calls = count_calls(secrets, "before-call.secrets-manager.GetSecretValue")
    loader = make_loader()

    loader.load()
    clock.now += 300
    loader.load()  # TTL expired
    loader.invalidate()
    loader.load()  # e.g. after a 401 because the secret was rotated

    assert len(calls) == 3


def test_picks_up_a_rotated_secret_after_invalidate(
    make_loader: Callable[..., ConfigLoader], secrets: SecretsManagerClient
) -> None:
    loader = make_loader()
    loader.load()
    secrets.put_secret_value(
        SecretId=SECRET_ID, SecretString=json.dumps(DB_SECRET | {"password": "new-Pa55"})
    )

    assert loader.load().db.password.get_secret_value() == DB_SECRET["password"]  # cached
    loader.invalidate()
    assert loader.load().db.password.get_secret_value() == "new-Pa55"


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"secret_id": "agent/missing"}, "secret 'agent/missing': not found"),
        ({"key": "features/missing.json"}, f"s3://{BUCKET}/features/missing.json: not found"),
        ({"bucket": "no-such-bucket"}, "bucket not found"),
    ],
    ids=["missing-secret", "missing-object", "missing-bucket"],
)
def test_missing_resources_raise_config_error(
    make_loader: Callable[..., ConfigLoader], overrides: dict[str, str], expected: str
) -> None:
    with pytest.raises(ConfigError, match=expected):
        make_loader(**overrides).load()


def _assert_secret_not_reachable(exc: BaseException, secret: str) -> None:
    """Check what an error tracker could capture: the printed traceback AND the linked
    exceptions (`__cause__` / `__context__`), whose attributes may hold the raw input."""
    assert secret not in "".join(traceback.format_exception(exc))
    assert exc.__cause__ is None
    assert exc.__context__ is None


def test_malformed_secret_never_leaks_its_value(
    make_loader: Callable[..., ConfigLoader], secrets: SecretsManagerClient
) -> None:
    secrets.put_secret_value(SecretId=SECRET_ID, SecretString="password=hunter2-not-json")

    with pytest.raises(ConfigError, match="Invalid JSON") as err:
        make_loader().load()

    _assert_secret_not_reachable(err.value, "hunter2")


def test_wrong_secret_shape_names_fields_but_not_values(
    make_loader: Callable[..., ConfigLoader], secrets: SecretsManagerClient
) -> None:
    secrets.put_secret_value(
        SecretId=SECRET_ID, SecretString=json.dumps({"username": "a", "password": "hunter2"})
    )

    with pytest.raises(ConfigError, match="host: Field required") as err:
        make_loader().load()

    _assert_secret_not_reachable(err.value, "hunter2")


def test_invalid_feature_config_is_rejected(
    make_loader: Callable[..., ConfigLoader], s3: S3Client
) -> None:
    s3.put_object(Bucket=BUCKET, Key=KEY, Body=b'{"model_id": "m", "max_tokens": 0}')

    with pytest.raises(ConfigError, match="max_tokens: Input should be greater than 0"):
        make_loader().load()


def test_access_denied_gives_an_actionable_hint() -> None:
    """moto doesn't enforce IAM by default, so error codes it can't produce are easiest to
    test with botocore's Stubber: it returns exactly the response you queue."""
    secrets = boto3.client("secretsmanager", region_name=REGION)
    s3 = boto3.client("s3", region_name=REGION)
    loader = ConfigLoader(
        secrets_client=secrets, s3_client=s3, secret_id=SECRET_ID, bucket=BUCKET, key=KEY
    )

    with Stubber(secrets) as stub:
        stub.add_client_error(
            "get_secret_value",
            service_error_code="AccessDeniedException",
            http_status_code=400,
            expected_params={"SecretId": SECRET_ID},
        )
        with pytest.raises(ConfigError, match="check the role's IAM policy"):
            loader.load()
        stub.assert_no_pending_responses()
