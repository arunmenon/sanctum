"""Authentication and the access rule every hub tool applies (plan decision 4).

Search applies the same rule inside SQL (`index.py`); gets and lists use `readable`.
Any token problem and any unreadable or unknown item become the same
`denied_or_not_found` error, so a caller cannot tell a restricted item from a missing one.
"""
from __future__ import annotations

from typing import Optional

from .corpus import HubRow
from .interfaces import TokenClaims, TokenRejected, TokenVerifier, denied_or_not_found


def authenticate(verifier: TokenVerifier, token: Optional[str], hub_id: str) -> TokenClaims:
    try:
        return verifier.verify(token, audience=hub_id)
    except TokenRejected:
        raise denied_or_not_found() from None


def readable(row: HubRow, claims: TokenClaims, principal_scoped: bool) -> bool:
    if not set(row.acl) & set(claims.groups):
        return False
    return not principal_scoped or row.owner == claims.sub
