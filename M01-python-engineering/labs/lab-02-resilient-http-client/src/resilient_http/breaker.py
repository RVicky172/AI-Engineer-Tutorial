import time
from collections.abc import Callable
from enum import StrEnum

from resilient_http.errors import CircuitOpenError


class BreakerState(StrEnum):
    CLOSED = "closed"  # normal: requests flow, failures are counted
    OPEN = "open"  # failing fast: no requests until reset_timeout passes
    HALF_OPEN = "half_open"  # one probe request decides: CLOSED on success, OPEN on failure


class CircuitBreaker:
    """Stops hammering a dependency that is clearly down, and gives it time to recover.

    Not thread-safe; one instance per event loop is the intended use.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._clock = clock
        self._state = BreakerState.CLOSED
        self._consecutive_failures = 0
        self._opened_at = 0.0
        self._probe_in_flight = False

    @property
    def state(self) -> BreakerState:
        if (
            self._state is BreakerState.OPEN
            and self._clock() - self._opened_at >= self.reset_timeout
        ):
            self._state = BreakerState.HALF_OPEN
        return self._state

    def before_call(self) -> None:
        """Raise CircuitOpenError if this call must not go out."""
        state = self.state
        if state is BreakerState.OPEN:
            raise CircuitOpenError(self.reset_timeout - (self._clock() - self._opened_at))
        if state is BreakerState.HALF_OPEN:
            if self._probe_in_flight:  # only one probe at a time
                raise CircuitOpenError(0.0)
            self._probe_in_flight = True

    def record_success(self) -> None:
        self._state = BreakerState.CLOSED
        self._consecutive_failures = 0
        self._probe_in_flight = False

    def record_failure(self) -> None:
        self._probe_in_flight = False
        if self._state is BreakerState.HALF_OPEN:
            self._open()
            return
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.failure_threshold:
            self._open()

    def abandon_probe(self) -> None:
        """The call ended without telling us anything about health (e.g. it was cancelled).

        Frees the half-open probe slot; without this the breaker would reject forever.
        """
        self._probe_in_flight = False

    def _open(self) -> None:
        self._state = BreakerState.OPEN
        self._opened_at = self._clock()
