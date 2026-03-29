import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import get_settings

settings = get_settings()

transport = ASGITransport(app=app)

@pytest.fixture
def client():
    return AsyncClient(transport=transport, base_url="http://test")

# ── Health ──────────────────────────────────────────────
@pytest.mark.anyio
async def test_health(client):
    async with client as c:
        r = await c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

# ── Public catalog ───────────────────────────────────────
@pytest.mark.anyio
@pytest.mark.integration
@pytest.mark.skip(reason="integration: requires live DB")
async def test_list_products_returns_schema(client):
    # Route exists and returns correct schema shape
    # (empty DB is acceptable for smoke test)
    async with client as c:
        r = await c.get("/v1/public/products?limit=5")
    assert r.status_code in (200, 503)  # 503 if DB not running
    if r.status_code == 200:
        data = r.json()
        assert "items" in data
        assert "next_cursor" in data
        assert "x-total-count" in r.headers

@pytest.mark.anyio
@pytest.mark.integration
@pytest.mark.skip(reason="integration: requires live DB")
async def test_product_detail_404(client):
    async with client as c:
        r = await c.get("/v1/public/products/00000000-0000-0000-0000-000000000000")
    assert r.status_code in (404, 503)

# ── Admin auth ───────────────────────────────────────────
@pytest.mark.anyio
async def test_admin_login_wrong_password(client):
    async with client as c:
        r = await c.post("/v1/admin/auth/login",
                         json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401

@pytest.mark.anyio
async def test_admin_login_success(client):
    async with client as c:
        r = await c.post("/v1/admin/auth/login",
                         json={"username": settings.admin_username,
                               "password": settings.admin_password})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.anyio
async def test_admin_requires_auth(client):
    async with client as c:
        r = await c.get("/v1/admin/sellers")
    assert r.status_code in (401, 422)

# ── Agent layer ──────────────────────────────────────────
@pytest.mark.anyio
async def test_agent_context(client):
    async with client as c:
        r = await c.get("/v1/agent/context")
    assert r.status_code == 200
    data = r.json()
    assert "capabilities" in data
    assert "api_version" in data
    assert len(data["capabilities"]) >= 2

@pytest.mark.anyio
@pytest.mark.integration
@pytest.mark.skip(reason="integration: requires live DB")
async def test_agent_search_schema(client):
    async with client as c:
        r = await c.post("/v1/agent/search",
                         json={"query": "test", "limit": 3})
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        assert isinstance(r.json(), list)
        assert "x-query-interpreted" in r.headers

@pytest.mark.anyio
async def test_llms_txt(client):
    async with client as c:
        r = await c.get("/llms.txt")
    assert r.status_code == 200
    assert "Kodex" in r.text
    assert "/v1/agent/search" in r.text
    assert "text/plain" in r.headers["content-type"]
