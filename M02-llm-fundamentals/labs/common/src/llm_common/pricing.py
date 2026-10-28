from dataclasses import dataclass

from anthropic.types import Usage


@dataclass(frozen=True)
class Price:
    """USD per 1M tokens."""

    input: float
    output: float
    cache_read: float
    cache_write: float  # 5-minute TTL write (1.25x input)


# Claude API list prices, checked 2026-10. Prices change: confirm on the pricing page before you
# quote a number to anyone. Bedrock bills separately (see its pricing page).
PRICES: dict[str, Price] = {
    "claude-opus-5-5": Price(input=4.00, output=20.00, cache_read=0.20, cache_write=5.00),
    "claude-sonnet-5-5": Price(input=2.00, output=10.00, cache_read=0.20, cache_write=2.50),
    # Haiku 5.5: prompts up to 100K tokens. Cache prices assumed at the usual 0.1x / 1.25x.
    "claude-haiku-5-5": Price(input=0.10, output=0.50, cache_read=0.01, cache_write=0.125),
    "claude-opus-5": Price(input=5.00, output=25.00, cache_read=0.50, cache_write=6.25),
    "claude-sonnet-5": Price(input=2.00, output=10.00, cache_read=0.20, cache_write=2.50),
}


def bare_model_id(model: str) -> str:
    """`us.anthropic.claude-opus-5-5` and `anthropic.claude-opus-5-5` -> `claude-opus-5-5`."""
    return model.rsplit("anthropic.", 1)[-1]


def price_for(model: str) -> Price:
    try:
        return PRICES[bare_model_id(model)]
    except KeyError:
        raise KeyError(f"No price for {model!r}: add it to llm_common.pricing.PRICES") from None


def thinking_tokens(usage: Usage) -> int:
    details = usage.output_tokens_details
    return details.thinking_tokens if details and details.thinking_tokens else 0


def cost_usd(model: str, usage: Usage) -> float:
    """`input_tokens` excludes cached tokens, so the three input buckets never double count.
    `output_tokens` already includes thinking tokens: you pay for reasoning you never see."""
    p = price_for(model)
    return (
        usage.input_tokens * p.input
        + (usage.cache_read_input_tokens or 0) * p.cache_read
        + (usage.cache_creation_input_tokens or 0) * p.cache_write
        + usage.output_tokens * p.output
    ) / 1_000_000


@dataclass
class UsageTally:
    """Running totals across many calls. Read tokens from `usage`; never estimate them."""

    model: str
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    cost_usd: float = 0.0

    def add(self, usage: Usage) -> float:
        cost = cost_usd(self.model, usage)
        self.calls += 1
        self.input_tokens += usage.input_tokens
        self.output_tokens += usage.output_tokens
        self.thinking_tokens += thinking_tokens(usage)
        self.cache_read_tokens += usage.cache_read_input_tokens or 0
        self.cache_write_tokens += usage.cache_creation_input_tokens or 0
        self.cost_usd += cost
        return cost

    def merge(self, other: "UsageTally") -> None:
        self.calls += other.calls
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.thinking_tokens += other.thinking_tokens
        self.cache_read_tokens += other.cache_read_tokens
        self.cache_write_tokens += other.cache_write_tokens
        self.cost_usd += other.cost_usd

    def per_call(self, total: int) -> float:
        return total / self.calls if self.calls else 0.0
