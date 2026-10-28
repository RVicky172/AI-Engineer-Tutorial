from llm_common.fake import FakeMessages, make_message, real_sdk_messages

from ragkit.generation import NO_ANSWER, answer, build_request, check_citations
from ragkit.store import Hit

HITS = [
    Hit("kb-a#0", "kb-a", "Reset at id.acme.example/reset.", 0.9),
    Hit("kb-b#1", "kb-b", "Call 4357.", 0.8),
]


def test_request_puts_each_chunk_in_a_tagged_document() -> None:
    req = build_request("How?", HITS, model="m")
    content = req["messages"][0]["content"]
    assert '<document doc_id="kb-a">\nReset at id.acme.example/reset.\n</document>' in content
    assert content.endswith("<question>How?</question>")
    assert not {"temperature", "top_p"} & req.keys()
    api, sent = real_sdk_messages(make_message("ok"))
    api.create(**req)
    assert sent[0]["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_citation_check() -> None:
    good = check_citations("Use the reset page [kb-a]. Or call [kb-b] [kb-a].", HITS)
    assert good.ok and good.cited == ("kb-a", "kb-b")

    invented = check_citations("Per policy [pol-passwords].", HITS)
    assert not invented.ok and invented.not_in_context == ("pol-passwords",)

    uncited = check_citations("Just reset it.", HITS)
    assert not uncited.ok

    declined = check_citations(NO_ANSWER, HITS)
    assert declined.ok and declined.declined


def test_answer_calls_the_model_and_checks_citations() -> None:
    fake = FakeMessages([make_message("Reset it [kb-a]."), make_message(stop_reason="refusal")])
    result = answer(fake, "How?", HITS, model="m")
    assert result.citations.ok and result.usage is not None
    refused = answer(fake, "How?", HITS, model="m")
    assert refused.text == "(the model declined to answer)" and not refused.citations.ok
