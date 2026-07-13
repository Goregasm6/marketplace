from __future__ import annotations

import re
import socket
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlparse
from urllib.request import Request, urlopen

from loguru import logger

from collectors.base import BaseCollector
from database.models import Listing, ListingStatus


class CraigslistHTMLParser(HTMLParser):
    """Parse Craigslist search-result markup into lightweight listing payloads."""

    def __init__(self) -> None:
        super().__init__()
        self.items: list[dict[str, str]] = []
        self._current_item: dict[str, str] | None = None
        self._inside_title = False
        self._inside_price = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name: value or "" for name, value in attrs}
        classes = set(attr_map.get("class", "").split())

        if tag == "li" and classes & {"result-row", "cl-static-search-result", "result"}:
            self._current_item = {"title": "", "url": "", "price": ""}
            return

        if self._current_item is None:
            return

        if tag == "a" and "result-title" in classes:
            self._inside_title = True
            href = attr_map.get("href", "")
            if href:
                self._current_item["url"] = href
            return

        if tag == "span" and "result-price" in classes:
            self._inside_price = True

    def handle_endtag(self, tag: str) -> None:
        if self._current_item is None:
            return

        if tag == "li":
            if self._current_item.get("title") and self._current_item.get("url"):
                self.items.append(self._current_item)
            self._current_item = None
            self._inside_title = False
            self._inside_price = False
            return

        if tag == "a":
            self._inside_title = False
            return

        if tag == "span":
            self._inside_price = False

    def handle_data(self, data: str) -> None:
        if self._current_item is None:
            return

        text = data.strip()
        if not text:
            return

        if self._inside_title:
            self._current_item["title"] = self._current_item.get("title", "") + text
        elif self._inside_price:
            self._current_item["price"] = self._current_item.get("price", "") + text


class CraigslistCollector(BaseCollector):
    """Collector implementation for Craigslist search results."""

    name = "craigslist"

    def __init__(
        self,
        *,
        base_url: str = "https://www.craigslist.org",
        search_path: str = "/search/sss",
        location: str | None = None,
        request_delay: float = 2.0,
        max_retries: int = 2,
        obey_robots: bool = True,
        user_agent: str = "Mozilla/5.0",
        seen_ids: Iterable[str] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.search_path = search_path
        self.location = location
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.obey_robots = obey_robots
        self.user_agent = user_agent
        self._seen_ids: set[str] = set(seen_ids or [])
        self._logger = logger.bind(component="craigslist_collector")

    def _build_search_url(self, query: str, *, location: str | None = None) -> str:
        if location and "." not in location:
            host = f"https://{location}.craigslist.org"
        elif location:
            host = location
        else:
            host = self.base_url
        return f"{host}{self.search_path}?query={quote(query)}"

    def _read_fixture(self, fixture_path: str | None) -> str | None:
        if not fixture_path:
            return None
        path = Path(fixture_path)
        if not path.exists():
            raise FileNotFoundError(f"Fixture not found: {fixture_path}")
        return path.read_text(encoding="utf-8")

    def _is_allowed_by_robots(self, url: str) -> bool:
        if not self.obey_robots:
            return True

        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        request = Request(robots_url, headers={"User-Agent": self.user_agent})

        try:
            with urlopen(request, timeout=10) as response:
                robots_text = response.read().decode("utf-8", errors="ignore")
        except (HTTPError, URLError, TimeoutError, socket.timeout):
            self._logger.warning("robots_check_failed", url=robots_url)
            return True

        user_agent = self.user_agent.lower()
        allowed = True
        current_agent: str | None = None

        for line in robots_text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            if stripped.lower().startswith("user-agent:"):
                current_agent = stripped.split(":", 1)[1].strip().lower()
                continue

            if not stripped.lower().startswith("disallow:") or current_agent is None:
                continue

            if current_agent not in {"*", user_agent}:
                continue

            path = stripped.split(":", 1)[1].strip()
            if path in {"", "/"}:
                allowed = False
                break

            if parsed.path.startswith(path):
                allowed = False
                break

        return allowed

    def _fetch_html(self, url: str, *, fixture_path: str | None = None) -> str:
        fixture_content = self._read_fixture(fixture_path)
        if fixture_content is not None:
            self._logger.info("fixture_loaded", url=url, fixture_path=fixture_path)
            return fixture_content

        if not self._is_allowed_by_robots(url):
            raise RuntimeError(f"Request disallowed by robots.txt for {url}")

        if self.request_delay > 0:
            time.sleep(self.request_delay)

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 2):
            try:
                request = Request(url, headers={"User-Agent": self.user_agent, "Accept": "text/html"})
                with urlopen(request, timeout=10) as response:
                    body = response.read().decode("utf-8", errors="ignore")
                self._logger.info("request_succeeded", url=url, attempt=attempt)
                return body
            except (HTTPError, URLError, TimeoutError, socket.timeout) as exc:
                last_error = exc
                self._logger.warning("request_failed", url=url, attempt=attempt, error=str(exc))
                if attempt > self.max_retries:
                    break
                if self.request_delay > 0:
                    time.sleep(self.request_delay * attempt)

        raise RuntimeError(f"Unable to fetch Craigslist results for {url}") from last_error

    def search(self, query: str, **kwargs: Any) -> str:
        url = kwargs.get("url") or self._build_search_url(query, location=kwargs.get("location", self.location))
        html = self._fetch_html(url, fixture_path=kwargs.get("fixture_path"))
        self._logger.info("search_completed", query=query, source=self.name, url=url, length=len(html))
        return html

    def fetch(self, search_results: Any, **kwargs: Any) -> list[dict[str, Any]]:
        if isinstance(search_results, str):
            parser = CraigslistHTMLParser()
            parser.feed(search_results)
            return [self._shape_listing(item, base_url=kwargs.get("base_url", self.base_url)) for item in parser.items]

        if isinstance(search_results, list):
            return [self._shape_listing(item, base_url=kwargs.get("base_url", self.base_url)) for item in search_results]

        return []

    def normalize(self, item: Any, **kwargs: Any) -> Listing:
        if isinstance(item, Listing):
            return item

        payload = dict(item)
        title = (payload.get("title") or "").strip()
        price = self._parse_price(payload.get("price"))
        external_id = self._extract_external_id(payload.get("url") or "")
        url = self._absolute_url(payload.get("url") or "", base_url=kwargs.get("base_url", self.base_url))

        return Listing(
            title=title,
            description=None,
            price=price,
            source="craigslist",
            external_id=external_id,
            url=url,
            status=ListingStatus.NEW,
        )

    def validate(self, item: Listing, **kwargs: Any) -> bool:
        return isinstance(item, Listing) and bool(item.title) and item.price >= 0 and bool(item.external_id or item.url)

    def save(self, items: Iterable[Any], **kwargs: Any) -> list[Listing]:
        saved: list[Listing] = []
        for item in items:
            listing = item if isinstance(item, Listing) else self.normalize(item, **kwargs)
            if not self.validate(listing, **kwargs):
                continue

            key = listing.external_id or listing.url or listing.title
            if key in self._seen_ids:
                continue

            self._seen_ids.add(key)
            saved.append(listing)

        return saved

    def _shape_listing(self, item: Mapping[str, Any], *, base_url: str) -> dict[str, Any]:
        title = (item.get("title") or "").strip()
        url = self._absolute_url(item.get("url") or "", base_url=base_url)
        return {"title": title, "url": url, "price": item.get("price", "")}

    def _absolute_url(self, href: str, *, base_url: str) -> str:
        if not href:
            return ""
        if href.startswith("http"):
            return href
        return urljoin(f"{base_url.rstrip('/')}/", href.lstrip("/"))

    def _extract_external_id(self, href: str) -> str | None:
        match = re.search(r"/(\d+)(?:\.html)?$", href)
        if match:
            return match.group(1)
        return None

    def _parse_price(self, value: Any) -> float:
        if value in (None, ""):
            return 0.0

        cleaned = re.sub(r"[^0-9.\-]", "", str(value))
        if not cleaned:
            return 0.0
        return float(cleaned)


__all__ = ["CraigslistCollector", "CraigslistHTMLParser"]
