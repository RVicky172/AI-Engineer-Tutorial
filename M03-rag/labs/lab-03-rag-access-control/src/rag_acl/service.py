"""The request path of a permission-aware assistant: token -> user -> filtered retrieval -> answer.

The model never sees group names and never decides what may be retrieved. By the time the
question reaches the model, the context already contains only what this user may read."""

from llm_common import MessagesAPI

from rag_acl.identity import authenticate
from rag_acl.retriever import Mode, SecureRetriever
from ragkit.generation import NO_ANSWER, Answer, answer, check_citations


def ask(
    api: MessagesAPI,
    retriever: SecureRetriever,
    token: str,
    question: str,
    *,
    model: str,
    mode: Mode = Mode.HYBRID,
    k: int = 5,
) -> Answer:
    user = authenticate(token)  # raises before any retrieval if the token is bad
    hits = retriever.search(user, question, mode, k)
    if not hits:
        # Nothing this user may read matches: answer without a model call, and say the same
        # thing whether restricted documents exist or not (don't confirm they exist).
        return Answer(NO_ANSWER, check_citations(NO_ANSWER, []))
    return answer(api, question, hits, model=model)
