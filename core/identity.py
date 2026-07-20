"""
Service for managing networking identities, rotation, and policies.

This service ensures that requests from collectors have varied signatures
to avoid simple automated request detection while respecting platform policies.

Ethical and Legal Considerations:
1. Respect robots.txt: The service includes robots.txt awareness and should be configured
   to obey it (obey_robots=True).
2. Rate Limiting: Randomized delays are implemented to avoid overwhelming servers.
3. Transparency: While signatures are rotated, the goal is not malicious evasion but
   maintaining stable access to public data.
4. Terms of Service: Users should be aware of the ToS of the platforms they are
   monitoring. This tool provides mechanisms for compliance (like robots.txt and
   delay management) but does not guarantee compliance with all platform-specific rules.
5. Data Privacy: Ensure collected data is public and does not infringe on personal privacy.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from pydantic import BaseModel, Field
from loguru import logger

from config.settings import settings


class HeaderProfile(BaseModel):
    """Configuration for a specific category of request headers."""

    name: str
    user_agents: List[str]
    accept_languages: List[str] = Field(
        default_factory=lambda: ["en-US,en;q=0.9", "en-GB,en;q=0.8"]
    )
    accept_encodings: List[str] = Field(default_factory=lambda: ["gzip, deflate, br"])
    extra_headers: Dict[str, str] = Field(default_factory=dict)


DEFAULT_PROFILES = [
    HeaderProfile(
        name="desktop_chrome",
        user_agents=[
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ],
        extra_headers={
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
        },
    ),
    HeaderProfile(
        name="desktop_firefox",
        user_agents=[
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        ],
        extra_headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1",
        },
    ),
    HeaderProfile(
        name="mobile_safari",
        user_agents=[
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        ],
        extra_headers={
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        },
    ),
]


class IdentityPolicy(BaseModel):
    """Collector-specific policy for request identity."""

    name: str
    rotate_ua: bool = True
    rotate_language: bool = True
    min_delay: float = 1.0
    max_delay: float = 5.0
    use_proxies: bool = False
    obey_robots: bool = True
    allowed_profiles: List[str] = Field(
        default_factory=lambda: ["desktop_chrome", "desktop_firefox"]
    )


class RequestIdentity(BaseModel):
    """A generated identity for a single request or session."""

    headers: Dict[str, str]
    proxy: Optional[str] = None
    delay: float = 0.0


class RequestIdentityService:
    """
    Service for managing networking identities, rotation, and policies.

    This service ensures that requests from collectors have varied signatures
    to avoid simple automated request detection while respecting platform policies.
    """

    def __init__(
        self,
        profiles: Optional[List[HeaderProfile]] = None,
        proxies: Optional[List[str]] = None,
        policies: Optional[Dict[str, IdentityPolicy]] = None,
    ) -> None:
        self.profiles = profiles or DEFAULT_PROFILES
        self.proxies = proxies or (
            [settings.network_proxy] if settings.network_proxy else []
        )
        self.policies = policies or {}
        self._robots_cache: Dict[str, RobotFileParser] = {}
        self._client: Optional[httpx.AsyncClient] = None
        self._logger = logger.bind(component="identity_service")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=5)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def register_policy(self, policy: IdentityPolicy) -> None:
        """Register a new policy or update an existing one."""
        self.policies[policy.name] = policy
        self._logger.debug("policy_registered", name=policy.name)

    def get_policy(self, collector_name: str) -> IdentityPolicy:
        """Get the policy for a specific collector, or a default one."""
        if collector_name in self.policies:
            return self.policies[collector_name]

        return IdentityPolicy(name=collector_name)

    def generate_identity(self, collector_name: str) -> RequestIdentity:
        """
        Generate a new request identity based on collector policy.
        """
        policy = self.get_policy(collector_name)

        # Select profile
        allowed_profiles = [
            p for p in self.profiles if p.name in policy.allowed_profiles
        ]
        if not allowed_profiles:
            allowed_profiles = self.profiles

        profile = random.choice(allowed_profiles)

        # Build headers
        headers = {
            "User-Agent": random.choice(profile.user_agents)
            if policy.rotate_ua
            else profile.user_agents[0],
            "Accept-Language": random.choice(profile.accept_languages)
            if policy.rotate_language
            else profile.accept_languages[0],
            "Accept-Encoding": random.choice(profile.accept_encodings),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Connection": "keep-alive",
        }
        headers.update(profile.extra_headers)

        # Select proxy
        proxy = (
            random.choice(self.proxies) if policy.use_proxies and self.proxies else None
        )

        # Calculate delay
        delay = random.uniform(policy.min_delay, policy.max_delay)

        return RequestIdentity(headers=headers, proxy=proxy, delay=delay)

    async def is_allowed(self, url: str, collector_name: str) -> bool:
        """
        Check if a URL is allowed by robots.txt for the given collector.
        """
        policy = self.get_policy(collector_name)
        if not policy.obey_robots:
            return True

        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = f"{base_url}/robots.txt"

        if base_url not in self._robots_cache:
            parser = RobotFileParser()
            parser.set_url(robots_url)
            try:
                client = await self._get_client()
                resp = await client.get(robots_url)
                if resp.status_code == 200:
                    parser.parse(resp.text.splitlines())
                else:
                    parser.disallow_all = False  # If no robots.txt, assume allowed
            except Exception as e:
                self._logger.warning(
                    "failed_to_fetch_robots", url=robots_url, error=str(e)
                )
                return True  # Fail open

            self._robots_cache[base_url] = parser

        user_agent = policy.name  # Or we could use the actual UA from identity
        return self._robots_cache[base_url].can_fetch(user_agent, url)


# Global instance
identity_service = RequestIdentityService()
