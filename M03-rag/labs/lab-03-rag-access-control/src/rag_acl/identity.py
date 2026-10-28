"""Who is asking. Groups come from the authenticated request, never from the model or the prompt.

In production the token is a verified JWT (signature, issuer, audience, expiry) and the groups
come from its claims or a directory lookup. Here a fixed table stands in for that, so tests can
log in as each persona. The important property is the same: `authenticate` is the ONLY way to
get a `User`, and nothing the user types can change its groups."""

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    user_id: str
    groups: frozenset[str]


DIRECTORY: dict[str, User] = {
    "tok-alice": User("alice", frozenset({"all-staff"})),
    "tok-bob": User("bob", frozenset({"all-staff", "it-ops"})),
    "tok-carol": User("carol", frozenset({"all-staff", "finance"})),
    "tok-dan": User("dan", frozenset({"all-staff", "hr"})),
    "tok-erin": User("erin", frozenset({"all-staff", "it-ops", "security"})),
    "tok-frank": User("frank", frozenset({"contractor"})),  # matches no document: sees nothing
}


class AuthenticationError(Exception):
    pass


def authenticate(token: str, directory: dict[str, User] = DIRECTORY) -> User:
    try:
        return directory[token]
    except KeyError:
        raise AuthenticationError("unknown or expired token") from None
