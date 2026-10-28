# Lab 03 Notes — Test AWS code with moto

## What I built
`ConfigLoader`: loads database credentials from **Secrets Manager** and feature settings (model ID, max tokens, enabled tools) from **S3**, validates both with Pydantic, caches them with a TTL, and turns AWS errors into clear `ConfigError`s that **never contain the secret**. Tested entirely against moto's in-memory AWS, so no account and no cost, and it runs on any laptop or CI runner.

```
src/config_loader/loader.py   ConfigLoader, DatabaseCredentials (SecretStr), FeatureConfig, ConfigError
tests/conftest.py             no-real-AWS guard, moto fixtures, call counter via botocore events
tests/test_loader.py          12 tests, 100% coverage, each < 1 s
```

## Commands
```bash
cd M01-python-engineering/labs && source .venv/bin/activate && cd lab-03-moto-aws-testing
pytest && ruff check . && ruff format --check . && mypy src tests
pytest --durations=5      # show the slowest tests
```

Production usage (e.g. in the M01 chat service lifespan):
```python
loader = ConfigLoader(
    secrets_client=boto3.client("secretsmanager"),  # credentials come from the task/execution role
    s3_client=boto3.client("s3"),
    secret_id="agent/db",
    bucket="acme-agent-config",
    key="features/prod.json",
)
config = loader.load()
config.db.password.get_secret_value()  # the only way to read the real value: explicit and greppable
```

---

## Key learnings

### 1. Make it impossible to hit real AWS from tests
The autouse fixture `no_real_aws` sets fake keys, removes `AWS_PROFILE`, and points the credentials/config files at paths that don't exist. Even on a laptop with an admin profile, a test that escapes moto fails with an auth error instead of touching a real account. Pair it with `mock_aws()`, which intercepts every boto3 call in-process.

### 2. Inject clients, don't create them inside
`ConfigLoader` receives `secrets_client` and `s3_client`. The class never chooses region, profile or credentials. That makes it:
- testable (pass moto-backed or Stubber clients),
- portable (same code in Lambda, ECS, AgentCore; the *role* supplies credentials),
- explicit (the region decision lives in one place: where the client is built).

### 3. moto vs. Stubber: when to use each
| | **moto** (`mock_aws`) | **botocore Stubber** |
|---|---|---|
| What it is | an in-memory fake of AWS behaviour | a queue of exact responses you script |
| Best for | realistic flows: create secret → read → rotate → read again | error codes moto doesn't produce (`AccessDeniedException`, throttling), exact request assertions |
| Catches | logic bugs across several calls | "did I send exactly these parameters?" |
| Weakness | doesn't enforce IAM by default; not every API is perfect | you write every response by hand; easy to stub something AWS would never return |
In this lab, moto drives 11 tests and Stubber covers the `AccessDenied` case. That's the usual split.

### 4. Count API calls with botocore events
```python
client.meta.events.register("before-call.secrets-manager.GetSecretValue", handler)
```
This works with moto, Stubber and real AWS, so it's how we prove the cache works (5 loads → 1 API call). Note that the service name in event names is the **service ID** (`secrets-manager`), not the client name (`secretsmanager`).

### 5. Caching secrets and handling rotation
Fetching a secret on every request adds latency and cost and can hit API limits. Fetching once forever means a **rotated** password breaks you until restart. The middle ground:
- cache with a TTL (here 300 s),
- `invalidate()` when the downstream rejects the credentials (401 / auth error), then retry once.
The test `test_picks_up_a_rotated_secret_after_invalidate` shows the exact rotation flow. AWS also ships ready-made caching (the Secrets Manager caching library and the Lambda "Parameters and Secrets" extension).

### 6. Secrets leak through *errors*, not just logs
This was the most surprising lesson of the lab:
- `SecretStr` masks the value in `repr`/`str`/JSON, ✅
- **but** a Pydantic `ValidationError` prints the *input* (the raw dict, password included), ❌
- and `raise ConfigError(...) from None` only hides the original exception from the *printed* traceback. Python still links it as `__context__`, and error trackers (Sentry etc.) walk that chain. ❌

The fix is to compute a safe message (field names + reasons via `exc.errors(include_input=False)`) and **raise outside the `except` block**, so nothing is attached. The test helper `_assert_secret_not_reachable` checks the printed traceback **and** `__cause__`/`__context__`.

### 7. Map AWS errors by code, never by message
`exc.response["Error"]["Code"]` (`ResourceNotFoundException`, `NoSuchKey`, `AccessDeniedException`...) is a stable API. The human-readable message is not. Each code maps to a *what to check* hint, e.g. "check the role's IAM policy (and KMS key policy)". That turns a 2-hour hunt into a 2-minute fix (see M08).

### 8. Validate config at startup, fail loudly
`FeatureConfig` rejects `max_tokens: 0` at load time with `max_tokens: Input should be greater than 0`. A bad config should stop a deploy at startup (health check fails, rollback), not surface as a weird model error three hours later.

---

## Gotchas found while building this

| Problem | Fix / lesson |
|---|---|
| My first version used `from None` and claimed it stopped leaks. A mutation check plus a 5-line experiment showed the secret was still reachable via `__context__`. | Raise outside the `except` block. **Verify security claims with a test, not with confidence.** |
| JSON parse error and schema error needed two code paths | `model_validate_json` handles both: invalid JSON is just another `ValidationError` |
| mypy strict can't type-check boto3 | Added `boto3-stubs[s3,secretsmanager]` (typed `S3Client`, `SecretsManagerClient`). The stubs catch typos like `SecretID=` at type-check time. |
| First test takes ~0.75 s | One-time boto3 + moto import and warm-up; the other tests take ~0.1-0.4 s. Use `pytest --durations=5` to find slow tests before guessing. |
| ruff `S105/S106` (hard-coded passwords) in tests | Ignored for `tests/**` only, where obviously fake passwords are the point |

---

## Improve it yourself
1. **Async variant:** boto3 is synchronous. Calling `loader.load()` inside a FastAPI `async def` blocks the event loop (M01 self-check). Wrap it in `await asyncio.to_thread(loader.load)` in the chat service, and explain why it's acceptable *with* the cache.
2. **Thundering herd on expiry:** 50 concurrent requests arriving just after the TTL expires all fetch the secret. Add a lock so only one refreshes (single-flight, the same idea as the OAuth token cache in M07 Lab 02).
3. **Stale-while-revalidate:** if refreshing fails (Secrets Manager briefly unavailable), keep serving the cached value for a grace period and log a warning. When is that safe, and when is it not?
4. **Least privilege (M08 preview):** write the IAM policy this loader needs: one secret ARN for `GetSecretValue`, one S3 prefix for `GetObject`, `kms:Decrypt` only if the secret uses a customer-managed key.
5. **moto server mode:** run `moto_server` and point the AWS CLI at it with `--endpoint-url`. That's handy for manual testing of the whole chat service.

## What I'd explain in an interview
- "Tests can't reach real AWS: fake credentials, no profile, moto in-process. Stubber covers error codes moto doesn't emulate, like AccessDenied."
- "Secrets are cached with a TTL and invalidated on auth failure, so rotation doesn't need a restart."
- "Secrets can leak through exception chains, not only logs. I raise sanitized errors outside the except block and have a test that checks the full chain."
- "Clients are injected, so the role and region come from the runtime environment, not from the code."
