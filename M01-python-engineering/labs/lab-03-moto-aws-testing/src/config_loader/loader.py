import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client
from mypy_boto3_secretsmanager import SecretsManagerClient
from pydantic import BaseModel, Field, SecretStr, ValidationError


class ConfigError(Exception):
    """Configuration could not be loaded. Messages never contain secret values."""


class DatabaseCredentials(BaseModel):
    """Lives in Secrets Manager. SecretStr prints as '**********' in repr, str and logs."""

    username: str
    password: SecretStr
    host: str
    port: int = 5432


class FeatureConfig(BaseModel):
    """Lives in S3 as JSON: non-secret settings that ops can change without a deploy."""

    model_id: str
    max_tokens: int = Field(gt=0, le=8192)
    enabled_tools: list[str] = []


@dataclass(frozen=True)
class AppConfig:
    db: DatabaseCredentials
    features: FeatureConfig


# AWS error code -> what a human should check. The code is the stable part of a ClientError;
# the message text is not, so never branch on the message.
_HINTS = {
    "ResourceNotFoundException": "not found; check the name/ARN and the region",
    "NoSuchKey": "not found; check the key",
    "NoSuchBucket": "bucket not found; check the name and the account",
    "AccessDeniedException": "access denied; check the role's IAM policy (and KMS key policy)",
    "AccessDenied": "access denied; check the role's IAM policy and the bucket policy",
    "DecryptionFailure": "KMS could not decrypt it; check kms:Decrypt and the key policy",
}


class ConfigLoader:
    """Loads AppConfig and caches it for `ttl_seconds`.

    Clients are passed in (dependency injection): production code builds them from the task
    role; tests pass moto-backed or stubbed clients. The class never decides region or
    credentials itself, which keeps it testable and portable.
    """

    def __init__(
        self,
        *,
        secrets_client: SecretsManagerClient,
        s3_client: S3Client,
        secret_id: str,
        bucket: str,
        key: str,
        ttl_seconds: float = 300.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._secrets = secrets_client
        self._s3 = s3_client
        self.secret_id = secret_id
        self.bucket = bucket
        self.key = key
        self.ttl_seconds = ttl_seconds
        self._clock = clock
        self._cached: AppConfig | None = None
        self._loaded_at = 0.0

    def load(self) -> AppConfig:
        if self._cached is not None and self._clock() - self._loaded_at < self.ttl_seconds:
            return self._cached
        config = AppConfig(db=self._load_credentials(), features=self._load_features())
        self._cached, self._loaded_at = config, self._clock()
        return config

    def invalidate(self) -> None:
        """Call after an auth failure: the secret may have been rotated since we cached it."""
        self._cached = None

    def _load_credentials(self) -> DatabaseCredentials:
        where = f"secret {self.secret_id!r}"
        try:
            raw = self._secrets.get_secret_value(SecretId=self.secret_id)["SecretString"]
        except ClientError as exc:
            raise ConfigError(_describe(exc, where)) from exc
        try:
            return DatabaseCredentials.model_validate_json(raw)  # bad JSON is a ValidationError too
        except ValidationError as exc:
            problem = _fields(exc)
        # Raised OUTSIDE the except block on purpose. A ValidationError's text includes the
        # input (the secret!), and inside the block Python would attach it as __context__,
        # even with `from None` (that only hides it from the printed traceback). Error
        # trackers walk that chain. Out here, nothing is attached.
        raise ConfigError(f"{where} is invalid: {problem}")

    def _load_features(self) -> FeatureConfig:
        where = f"s3://{self.bucket}/{self.key}"
        try:
            body = self._s3.get_object(Bucket=self.bucket, Key=self.key)["Body"].read()
        except ClientError as exc:
            raise ConfigError(_describe(exc, where)) from exc
        try:
            return FeatureConfig.model_validate_json(body)
        except ValidationError as exc:
            # Not secret, so keeping the cause is fine and helps debugging.
            raise ConfigError(f"{where} is invalid: {_fields(exc)}") from exc


def _describe(exc: ClientError, where: str) -> str:
    code = exc.response.get("Error", {}).get("Code", "Unknown")
    return f"{where}: {_HINTS.get(code, 'AWS error')} ({code})"


def _fields(exc: ValidationError) -> str:
    """Field names and reasons only, never the input values."""
    errors: list[Any] = exc.errors(include_input=False, include_url=False)
    return "; ".join(f"{'.'.join(map(str, e['loc'])) or '<root>'}: {e['msg']}" for e in errors)
