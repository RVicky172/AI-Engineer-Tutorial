from pathlib import Path

import pytest
from anthropic import Anthropic, AnthropicBedrockMantle

from llm_common import Settings, UsageTally, cost_usd, make_messages_api, text_of, tool_uses
from llm_common.fake import FakeMessages, make_message, real_sdk_messages, tool_use_block
from llm_common.pricing import bare_model_id, price_for


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("LLM_PROVIDER", "LLM_MODEL", "AWS_REGION", "AWS_PROFILE"):
        monkeypatch.delenv(name, raising=False)


def test_settings_defaults_without_env() -> None:
    settings = Settings.from_env(env_file=None)
    assert settings == Settings(provider="anthropic", model="claude-opus-5-5")
    assert settings.api_model_id == "claude-opus-5-5"


def test_settings_reads_env_file_but_shell_wins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = tmp_path / ".env"
    env.write_text("LLM_PROVIDER=bedrock\nLLM_MODEL=claude-haiku-5-5\nAWS_REGION=us-west-2\n")
    monkeypatch.setenv("LLM_MODEL", "claude-sonnet-5-5")

    settings = Settings.from_env(env_file=env)

    assert settings.provider == "bedrock"
    assert settings.model == "claude-sonnet-5-5"
    assert settings.aws_region == "us-west-2"


def test_settings_rejects_unknown_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    with pytest.raises(ValueError, match="LLM_PROVIDER"):
        Settings.from_env(env_file=None)


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("claude-opus-5-5", "anthropic.claude-opus-5-5"),
        ("anthropic.claude-opus-5-5", "anthropic.claude-opus-5-5"),
        ("us.anthropic.claude-opus-5-5", "us.anthropic.claude-opus-5-5"),
    ],
)
def test_bedrock_model_ids_get_the_provider_prefix_once(model: str, expected: str) -> None:
    assert Settings(provider="bedrock", model=model).api_model_id == expected


def test_make_messages_api_picks_the_provider_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")  # constructing a client needs no network
    first_party = make_messages_api(Settings())
    assert isinstance(first_party._client, Anthropic)  # type: ignore[attr-defined]

    bedrock = make_messages_api(Settings(provider="bedrock", aws_region="us-east-1"))
    assert isinstance(bedrock._client, AnthropicBedrockMantle)  # type: ignore[attr-defined]


def test_cost_counts_each_input_bucket_once_and_includes_thinking() -> None:
    msg = make_message(
        "ok", input_tokens=1_000, output_tokens=500, thinking_tokens=300, cache_read_tokens=10_000
    )
    # opus-5-5: 1k x $4 + 10k x $0.20 + 500 x $20, per 1M tokens
    assert cost_usd("claude-opus-5-5", msg.usage) == pytest.approx(0.004 + 0.002 + 0.010)


def test_pricing_accepts_bedrock_ids_and_explains_unknown_models() -> None:
    assert bare_model_id("us.anthropic.claude-haiku-5-5") == "claude-haiku-5-5"
    assert price_for("anthropic.claude-haiku-5-5").input == 0.10
    with pytest.raises(KeyError, match="add it to"):
        price_for("gpt-9")


def test_usage_tally_accumulates_and_merges() -> None:
    a = UsageTally(model="claude-haiku-5-5")
    a.add(make_message("x", input_tokens=100, output_tokens=40, thinking_tokens=10).usage)
    a.add(make_message("y", input_tokens=300, output_tokens=60).usage)
    b = UsageTally(model="claude-haiku-5-5")
    b.add(make_message("z", input_tokens=200, output_tokens=0).usage)

    a.merge(b)

    assert (a.calls, a.input_tokens, a.output_tokens, a.thinking_tokens) == (3, 600, 100, 10)
    assert a.per_call(a.input_tokens) == 200
    assert UsageTally(model="claude-haiku-5-5").per_call(0) == 0.0
    assert a.cost_usd == pytest.approx((600 * 0.10 + 100 * 0.50) / 1_000_000)


def test_content_helpers_skip_thinking_blocks() -> None:
    msg = make_message(
        {"type": "thinking", "thinking": "", "signature": "sig"},
        "Looking it up. ",
        tool_use_block("get_ticket", {"number": "INC0012345"}, id="toolu_1"),
        "Done.",
    )
    assert text_of(msg) == "Looking it up. Done."
    assert [(t.name, t.input) for t in tool_uses(msg)] == [("get_ticket", {"number": "INC0012345"})]
    assert msg.stop_reason == "tool_use"


def test_fake_messages_replays_script_records_calls_and_raises() -> None:
    fake = FakeMessages([make_message("one"), RuntimeError("boom")])

    assert text_of(fake.create(model="m", messages=[])) == "one"
    with pytest.raises(RuntimeError, match="boom"):
        fake.create(model="m", messages=[])
    with pytest.raises(AssertionError, match="ran out"):
        fake.create(model="m", messages=[])
    assert len(fake.calls) == 3


def test_fake_messages_can_answer_from_the_request() -> None:
    fake = FakeMessages(lambda req: make_message(f"echo {req['messages'][0]['content']}"))
    assert text_of(fake.create(messages=[{"role": "user", "content": "hi"}])) == "echo hi"


def test_real_sdk_messages_records_the_serialised_request() -> None:
    api, sent = real_sdk_messages(make_message("pong", input_tokens=3))

    reply = api.create(
        model="claude-opus-5-5",
        max_tokens=64,
        messages=[{"role": "user", "content": "ping"}],
        output_config={"effort": "low"},
    )

    assert text_of(reply) == "pong"
    assert reply.usage.input_tokens == 3
    assert sent[0]["output_config"] == {"effort": "low"}
    assert sent[0]["_headers"]["anthropic-version"] == "2026-10-21"
