import random
from datetime import UTC, datetime

import pytest

from resilient_http.backoff import full_jitter, parse_retry_after


@pytest.mark.parametrize(("attempt", "ceiling"), [(0, 0.2), (1, 0.4), (2, 0.8), (6, 10.0)])
def test_full_jitter_stays_within_the_exponential_ceiling(attempt: int, ceiling: float) -> None:
    rng = random.Random(42)
    delays = [full_jitter(attempt, 0.2, 10.0, rng.uniform) for _ in range(500)]
    assert all(0.0 <= d <= ceiling for d in delays)
    # Spread is the whole point: delays must not cluster at one value.
    assert max(delays) - min(delays) > ceiling * 0.8


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("7", 7.0),
        (" 0 ", 0.0),
        ("Wed, 28 Oct 2026 12:00:30 GMT", 30.0),
        ("Wed, 28 Oct 2026 11:59:00 GMT", 0.0),  # date in the past -> no wait
        ("soon", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_retry_after(header: str | None, expected: float | None) -> None:
    now = datetime(2026, 10, 28, 12, 0, 0, tzinfo=UTC)
    assert parse_retry_after(header, now) == expected
