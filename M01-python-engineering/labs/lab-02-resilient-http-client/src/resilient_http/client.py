import asyncio
import random
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import httpx
import structlog

from resilient_http.backoff import full_jitter, parse_retry_after
from resilient_http.breaker import CircuitBreaker
from resilient_http.errors import RetriesExhaustedError

log = structlog.get_logger()

# HTTP semantics: repeating these has the same effect as sending them once.
IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})
RETRYABLE_STATUS = frozenset({429, 502, 503, 504})
# Module-level constant: a call in a default argument runs once at import (ruff B008).
DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=3.0)


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 4  # total attempts, including the first
    backoff_base: float = 0.2
    backoff_cap: float = 10.0
    # If the server asks us to wait longer than this, give up instead of blocking a caller
    # (an agent turn, a user request) for minutes.
    max_retry_after: float = 30.0
    # Overall time budget for one logical call across all attempts and sleeps.
    total_timeout: float | None = 60.0


class ResilientClient:
    """Wraps ONE shared httpx.AsyncClient (connection pooling) with resilience behaviour.

    Outcomes for a call:
    - final non-retryable response (2xx, 3xx, 4xx except 429) -> returned as-is
    - retryable failures until attempts/time run out          -> RetriesExhaustedError
    - breaker open                                            -> CircuitOpenError (no request)
    """

    def __init__(
        self,
        base_url: str = "",
        *,
        timeout: httpx.Timeout | float = DEFAULT_TIMEOUT,
        policy: RetryPolicy | None = None,
        breaker: CircuitBreaker | None = None,
        http_client: httpx.AsyncClient | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        clock: Callable[[], float] = time.monotonic,
        rand: Callable[[float, float], float] = random.uniform,
    ) -> None:
        self._http = http_client or httpx.AsyncClient(base_url=base_url, timeout=timeout)
        self.policy = policy or RetryPolicy()
        self.breaker = breaker or CircuitBreaker(clock=clock)
        # Injected so tests run instantly and deterministically (no real sleeping).
        self._sleep = sleep
        self._clock = clock
        self._rand = rand

    async def __aenter__(self) -> "ResilientClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self._http.aclose()

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    async def request(
        self,
        method: str,
        url: str,
        *,
        idempotency_key: str | None = None,
        # Same name and meaning as httpx's per-request timeout, so callers already know it.
        timeout: httpx.Timeout | float | None = None,  # noqa: ASYNC109
        **kwargs: Any,
    ) -> httpx.Response:
        """Send with retries.

        POST/PATCH are only fully retried when `idempotency_key` is given: without it, a
        retry after a timeout could create a second ticket or restart a service twice.
        The key must identify the *logical operation* (the same on every attempt) and the
        server must support it.
        """
        method = method.upper()
        headers = dict(kwargs.pop("headers", None) or {})
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        safe_to_repeat = method in IDEMPOTENT_METHODS or idempotency_key is not None
        if timeout is not None:
            kwargs["timeout"] = timeout

        policy = self.policy
        deadline = (
            self._clock() + policy.total_timeout if policy.total_timeout is not None else None
        )
        last_response: httpx.Response | None = None
        last_exception: Exception | None = None

        for attempt in range(policy.max_attempts):
            self.breaker.before_call()
            try:
                response = await self._http.request(method, url, headers=headers, **kwargs)
            except httpx.TransportError as exc:  # includes every httpx timeout
                self.breaker.record_failure()
                last_exception, last_response = exc, None
                # A connect failure means the request never reached the server, so it is
                # safe to retry even a POST. A read timeout might have been processed.
                never_sent = isinstance(exc, httpx.ConnectError | httpx.ConnectTimeout)
                if not (safe_to_repeat or never_sent):
                    raise
                reason = type(exc).__name__
                retry_after = None
            except BaseException:
                # Cancelled (or an unexpected bug): nothing learned about the dependency's
                # health, but a half-open probe slot must be freed or the breaker stays stuck.
                self.breaker.abandon_probe()
                raise
            else:
                if response.status_code not in RETRYABLE_STATUS:
                    # 4xx is the caller's problem, not the dependency's health.
                    if response.status_code < 500:
                        self.breaker.record_success()
                    return response
                # 429 is the server protecting itself: it is alive, so it counts as healthy for
                # the breaker (and frees a half-open probe). Retry-After handles the pacing.
                if response.status_code == 429:
                    self.breaker.record_success()
                else:
                    self.breaker.record_failure()
                last_response, last_exception = response, None
                # 429 means "not processed", so any method may retry; a 5xx might have been.
                if not (safe_to_repeat or response.status_code == 429):
                    return response
                reason = f"HTTP {response.status_code}"
                retry_after = parse_retry_after(response.headers.get("Retry-After"))

            if attempt == policy.max_attempts - 1:
                break
            if retry_after is not None and retry_after > policy.max_retry_after:
                raise RetriesExhaustedError(
                    f"server asked to wait {retry_after:.0f}s", attempt + 1, last_response
                )
            # Honour Retry-After exactly when given; otherwise back off with jitter.
            delay = (
                retry_after
                if retry_after is not None
                else full_jitter(attempt, policy.backoff_base, policy.backoff_cap, self._rand)
            )
            if deadline is not None and self._clock() + delay > deadline:
                raise RetriesExhaustedError(
                    "time budget exhausted", attempt + 1, last_response, last_exception
                )
            log.warning(
                "http.retry",
                method=method,
                url=url,
                attempt=attempt + 1,
                reason=reason,
                delay_s=round(delay, 3),
            )
            await self._sleep(delay)

        raise RetriesExhaustedError(
            "retries exhausted", policy.max_attempts, last_response, last_exception
        )
