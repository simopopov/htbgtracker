"""CHPP transport layer.

Two implementations behind one interface:

- CHPPHTTPClient — real OAuth 1.0a (HMAC-SHA1, GET) against chpp.hattrick.org.
  Only usable after Hattrick approves the CHPP application and keys exist.
- MockCHPPClient — reads XML fixtures from disk. The default in development;
  guarantees no request ever reaches hattrick.org before approval.

Fetch discipline (CHPP_TECHNICAL.md §7) is enforced one level up in
services/sync.py; this layer is deliberately dumb and sequential.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from ..config import settings
from .errors import CHPPError, error_for_code
from .parse import parse_error

CHPP_RESOURCE_URL = "https://chpp.hattrick.org/chppxml.ashx"
REQUEST_TOKEN_URL = "https://chpp.hattrick.org/oauth/request_token.ashx"
AUTHORIZE_URL = "https://chpp.hattrick.org/oauth/authorize.aspx"
ACCESS_TOKEN_URL = "https://chpp.hattrick.org/oauth/access_token.ashx"

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Which request parameter identifies the object, for fixture-file resolution.
_KEY_PARAM = {
    "playerdetails": "playerid",
    "teamdetails": "userid",
    "players": "teamid",
    "training": "teamid",
    "economy": "teamid",
    "stafflist": "teamid",
}


def _check(xml: str) -> str:
    root = ET.fromstring(xml)
    err = parse_error(root)
    if err is not None:
        code, message = err
        raise error_for_code(code, message or "")
    return xml


class MockCHPPClient:
    def fetch(self, file: str, version: str, **params) -> str:
        key_param = _KEY_PARAM.get(file)
        obj_id = None
        if key_param:
            for k, v in params.items():
                if k.lower() == key_param:
                    obj_id = v
                    break
        name = f"{file}_{obj_id}.xml" if obj_id is not None else f"{file}.xml"
        path = FIXTURES_DIR / name
        if not path.exists():
            raise CHPPError(-1, f"mock: no fixture {name}")
        return _check(path.read_text(encoding="utf-8"))


class CHPPHTTPClient:
    def __init__(self, access_token: str | None = None, access_secret: str | None = None):
        from requests_oauthlib import OAuth1Session

        if not settings.chpp_consumer_key:
            raise CHPPError(-1, "CHPP consumer key not configured")
        self.session = OAuth1Session(
            settings.chpp_consumer_key,
            client_secret=settings.chpp_consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_secret,
        )

    def fetch(self, file: str, version: str, **params) -> str:
        query = {"file": file, "version": version}
        query.update({k: v for k, v in params.items() if v is not None})
        resp = self.session.get(
            CHPP_RESOURCE_URL,
            params=query,
            headers={"User-Agent": f"{settings.app_name}/{settings.app_version}"},
            timeout=20,
        )
        resp.raise_for_status()
        return _check(resp.text)


def get_client(access_token: str | None = None, access_secret: str | None = None):
    if settings.chpp_mock:
        return MockCHPPClient()
    return CHPPHTTPClient(access_token, access_secret)


# --- OAuth 1.0a flow helpers (real mode only) --------------------------------

def oauth_request_token(callback_url: str) -> dict:
    from requests_oauthlib import OAuth1Session

    session = OAuth1Session(
        settings.chpp_consumer_key,
        client_secret=settings.chpp_consumer_secret,
        callback_uri=callback_url,
    )
    return session.fetch_request_token(REQUEST_TOKEN_URL)


def oauth_authorize_url(request_token: str) -> str:
    # Read access needs no scope; this project deliberately requests none.
    return f"{AUTHORIZE_URL}?oauth_token={request_token}"


def oauth_access_token(request_token: str, request_secret: str, verifier: str) -> dict:
    from requests_oauthlib import OAuth1Session

    session = OAuth1Session(
        settings.chpp_consumer_key,
        client_secret=settings.chpp_consumer_secret,
        resource_owner_key=request_token,
        resource_owner_secret=request_secret,
        verifier=verifier,
    )
    return session.fetch_access_token(ACCESS_TOKEN_URL)
