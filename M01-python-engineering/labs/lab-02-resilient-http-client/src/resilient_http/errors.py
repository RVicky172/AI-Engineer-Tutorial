import httpx


class CircuitOpenError(Exception):
    """Raised without making a request: the dependency recently failed too often."""

    def __init__(self, retry_in_seconds: float) -> None:
        super().__init__(f"circuit open; next probe allowed in {retry_in_seconds:.1f}s")
        self.retry_in_seconds = retry_in_seconds


class RetriesExhaustedError(Exception):
    """Every attempt failed with a retryable outcome, or the time budget ran out.

    Carries the last response or exception so callers (and logs) can see what happened.
    """

    def __init__(
        self,
        reason: str,
        attempts: int,
        last_response: httpx.Response | None = None,
        last_exception: Exception | None = None,
    ) -> None:
        super().__init__(f"{reason} after {attempts} attempt(s)")
        self.reason = reason
        self.attempts = attempts
        self.last_response = last_response
        self.last_exception = last_exception
