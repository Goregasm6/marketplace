import asyncio
from unittest.mock import AsyncMock, patch
import pytest
from core.identity import RequestIdentityService, IdentityPolicy


@pytest.fixture
def identity_service():
    return RequestIdentityService()


def test_generate_identity_defaults(identity_service):
    identity = identity_service.generate_identity("test_collector")
    assert "User-Agent" in identity.headers
    assert "Accept-Language" in identity.headers
    assert "Accept-Encoding" in identity.headers
    assert identity.delay >= 1.0
    assert identity.delay <= 5.0


def test_custom_policy(identity_service):
    policy = IdentityPolicy(
        name="custom", min_delay=0.1, max_delay=0.2, rotate_ua=False
    )
    identity_service.register_policy(policy)

    identity = identity_service.generate_identity("custom")
    assert identity.delay >= 0.1
    assert identity.delay <= 0.2


def test_robots_allowed_mocked(identity_service):
    async def run_test():
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = AsyncMock(
                status_code=200, text="User-agent: *\nDisallow: /blocked"
            )

            allowed = await identity_service.is_allowed(
                "https://example.com/allowed", "test"
            )
            assert allowed is True

            disallowed = await identity_service.is_allowed(
                "https://example.com/blocked", "test"
            )
            assert disallowed is False

    asyncio.run(run_test())


def test_profile_selection(identity_service):
    policy = IdentityPolicy(name="only_chrome", allowed_profiles=["desktop_chrome"])
    identity_service.register_policy(policy)

    identity = identity_service.generate_identity("only_chrome")
    ua = identity.headers["User-Agent"]

    # Check if UA belongs to desktop_chrome profile
    chrome_uas = next(
        p.user_agents for p in identity_service.profiles if p.name == "desktop_chrome"
    )
    assert ua in chrome_uas
