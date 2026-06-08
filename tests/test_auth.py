# tests/test_auth.py
import pytest
from httpx import AsyncClient
from app.main import app
from unittest.mock import patch

@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

# Mock get_user_doc for protected endpoint
from app import crud

@pytest.mark.asyncio
async def test_protected_me(monkeypatch):
    fake_user = {"id":"uid123","email":"a@b.com","role":"student","name":"Alice"}
    monkeypatch.setattr(crud, "get_user_doc", lambda uid: fake_user)
    # create a token similarly to utils.create_access_token
    from app.utils import create_access_token
    token, _ = create_access_token("uid123", "student")
    headers = {"Authorization": f"Bearer {token}"}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/auth/me", headers=headers)
        assert r.status_code == 200
        assert r.json()["email"] == "a@b.com"
