import random
from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime


def full_jitter(
    attempt: int,
    base: float,
    cap: float,
    rand: Callable[[float, float], float] = random.uniform,
) -> float:
    """Delay before retry number `attempt` (0-based): uniform(0, min(cap, base * 2**attempt)).

    Without jitter, every client that failed at the same moment retries at the same moment
    and knocks the recovering service over again ("thundering herd"). Full jitter spreads
    them out; see AWS Builders' Library "Timeouts, retries and backoff with jitter".
    """
    return rand(0.0, min(cap, base * 2**attempt))


def parse_retry_after(value: str | None, now: datetime | None = None) -> float | None:
    """Retry-After is either delay-seconds ("120") or an HTTP date. Returns seconds, or None."""
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    now = now or datetime.now(UTC)
    return max(0.0, (when - now).total_seconds())
