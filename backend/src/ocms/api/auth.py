from __future__ import annotations

import logging
import time
from threading import Lock
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from ocms.config import Settings, get_settings

logger = logging.getLogger(__name__)

_security = HTTPBearer(auto_error=True)
_JWKS_REFRESH_INTERVAL = 3600  # seconds


class _JWKSCache:
    def __init__(self) -> None:
        self._client: PyJWKClient | None = None
        self._loaded_for: tuple[str, str] | None = None
        self._loaded_at: float = 0.0
        self._lock = Lock()

    def get(self, region: str, user_pool_id: str) -> PyJWKClient:
        key = (region, user_pool_id)
        now = time.time()
        with self._lock:
            stale = now - self._loaded_at > _JWKS_REFRESH_INTERVAL
            if self._client is None or self._loaded_for != key or stale:
                url = (
                    f"https://cognito-idp.{region}.amazonaws.com/"
                    f"{user_pool_id}/.well-known/jwks.json"
                )
                self._client = PyJWKClient(url, cache_keys=True)
                self._loaded_for = key
                self._loaded_at = now
            return self._client


_jwks_cache = _JWKSCache()


def _expected_issuer(settings: Settings) -> str:
    return (
        f"https://cognito-idp.{settings.effective_cognito_region}.amazonaws.com/"
        f"{settings.cognito_user_pool_id}"
    )


def verify_cognito_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
    settings: Settings = Depends(get_settings),
) -> str:
    """Validate a Cognito-issued access token and return the subject (user id).

    Raises 401 on any verification failure. The function is intentionally
    structured so test suites can replace it via `app.dependency_overrides`
    without needing a live Cognito User Pool.
    """
    token = credentials.credentials
    client = _jwks_cache.get(
        settings.effective_cognito_region, settings.cognito_user_pool_id
    )
    try:
        signing_key = client.get_signing_key_from_jwt(token).key
    except jwt.PyJWKClientError as exc:
        logger.warning("JWKS lookup failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signing key",
        ) from exc

    try:
        claims: dict[str, Any] = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=_expected_issuer(settings),
            options={"require": ["exp", "iss", "sub", "token_use"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc

    token_use = claims.get("token_use")
    if token_use != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unexpected token_use: {token_use!r}",
        )

    # Cognito access tokens carry the app client id in `client_id`, not `aud`.
    if claims.get("client_id") != settings.cognito_client_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token client_id mismatch",
        )

    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )
    return sub
