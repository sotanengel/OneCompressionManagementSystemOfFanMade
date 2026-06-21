from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ocms.api.auth import verify_cognito_jwt
from ocms.config import Settings


def _build_app() -> tuple[FastAPI, MagicMock]:
    from fastapi import Depends

    settings_mock = MagicMock(spec=Settings)
    settings_mock.cognito_user_pool_id = "us-east-1_TESTPOOL"
    settings_mock.cognito_client_id = "test-client-id"
    settings_mock.effective_cognito_region = "us-east-1"

    test_app = FastAPI()

    @test_app.get("/protected")
    def protected(user: str = Depends(verify_cognito_jwt)) -> dict[str, str]:
        return {"user": user}

    from ocms.config import get_settings

    test_app.dependency_overrides[get_settings] = lambda: settings_mock
    return test_app, settings_mock


def _make_signed_token(
    private_key: rsa.RSAPrivateKey,
    *,
    iss: str = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TESTPOOL",
    client_id: str = "test-client-id",
    token_use: str = "access",
    sub: str = "user-42",
    exp_delta: int = 600,
    kid: str = "test-kid",
) -> str:
    payload = {
        "iss": iss,
        "client_id": client_id,
        "token_use": token_use,
        "sub": sub,
        "exp": int(time.time()) + exp_delta,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": kid})


@pytest.fixture()
def rsa_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture()
def patch_jwks(rsa_key: rsa.RSAPrivateKey):
    signing_key = MagicMock()
    signing_key.key = rsa_key.public_key()
    with patch("ocms.api.auth._jwks_cache") as cache:
        client = MagicMock()
        client.get_signing_key_from_jwt.return_value = signing_key
        cache.get.return_value = client
        yield


def test_rejects_request_without_authorization() -> None:
    test_app, _ = _build_app()
    client = TestClient(test_app)
    resp = client.get("/protected")
    # Starlette's HTTPBearer responds 403 in newer versions; FastAPI's bundled
    # 401 fallback is also acceptable. Either way the request must be refused.
    assert resp.status_code in (401, 403)


def test_rejects_expired_token(
    rsa_key: rsa.RSAPrivateKey, patch_jwks: None
) -> None:
    test_app, _ = _build_app()
    client = TestClient(test_app)
    token = _make_signed_token(rsa_key, exp_delta=-60)
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


def test_rejects_wrong_client_id(
    rsa_key: rsa.RSAPrivateKey, patch_jwks: None
) -> None:
    test_app, _ = _build_app()
    client = TestClient(test_app)
    token = _make_signed_token(rsa_key, client_id="some-other-client")
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert "client_id" in resp.json()["detail"]


def test_rejects_id_token_instead_of_access(
    rsa_key: rsa.RSAPrivateKey, patch_jwks: None
) -> None:
    test_app, _ = _build_app()
    client = TestClient(test_app)
    token = _make_signed_token(rsa_key, token_use="id")
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert "token_use" in resp.json()["detail"]


def test_rejects_wrong_issuer(
    rsa_key: rsa.RSAPrivateKey, patch_jwks: None
) -> None:
    test_app, _ = _build_app()
    client = TestClient(test_app)
    token = _make_signed_token(rsa_key, iss="https://evil.example.com/")
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_accepts_valid_access_token(
    rsa_key: rsa.RSAPrivateKey, patch_jwks: None
) -> None:
    test_app, _ = _build_app()
    client = TestClient(test_app)
    token = _make_signed_token(rsa_key)
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == {"user": "user-42"}
