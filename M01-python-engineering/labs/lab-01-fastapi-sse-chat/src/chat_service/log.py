import logging

import structlog


def configure_logging(level: str = "INFO", json: bool = True) -> None:
    """One JSON object per log line, with request context merged in automatically.

    `merge_contextvars` is what makes `request_id` appear on every line: the middleware
    binds it once per request and every logger call in that request picks it up.
    """
    renderer: structlog.typing.Processor = (
        structlog.processors.JSONRenderer() if json else structlog.dev.ConsoleRenderer()
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelNamesMapping()[level.upper()]
        ),
        # Caching is faster but freezes the config on first use, which breaks tests that
        # reconfigure logging or capture output. The cost is negligible at this scale.
        cache_logger_on_first_use=False,
    )
