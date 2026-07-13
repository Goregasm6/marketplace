from __future__ import annotations

import json
from typing import Any, Callable
from urllib.error import URLError
from urllib.request import Request, urlopen

from alerts.notifications import AlertNotification, Notification


class DiscordNotification(Notification):
    """Send alerts to a Discord webhook endpoint."""

    def __init__(
        self,
        webhook_url: str | None = None,
        http_client: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        self.webhook_url = webhook_url
        self._http_client = http_client or self._post_json

    def send(self, alert: AlertNotification) -> None:
        if not self.webhook_url:
            return

        payload = self._build_payload(alert)
        self._http_client(self.webhook_url, payload)

    def _build_payload(self, alert: AlertNotification) -> dict[str, Any]:
        return {
            "content": f"New flip opportunity: {alert.title}",
            "embeds": [
                {
                    "title": alert.title,
                    "description": alert.reasoning,
                    "color": 3066993,
                    "fields": [
                        {"name": "Price", "value": self._money(alert.price), "inline": True},
                        {"name": "Estimated value", "value": self._money(alert.estimated_value), "inline": True},
                        {"name": "Expected profit", "value": self._money(alert.expected_profit), "inline": True},
                        {"name": "FlipScore", "value": str(alert.flip_score), "inline": True},
                        {"name": "Confidence", "value": f"{alert.confidence:.0%}", "inline": True},
                        {"name": "Reasoning", "value": alert.reasoning, "inline": False},
                        {"name": "Listing URL", "value": alert.listing_url, "inline": False},
                    ],
                }
            ],
        }

    @staticmethod
    def _money(value: float) -> str:
        return f"${value:,.2f}"

    @staticmethod
    def _post_json(url: str, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=10) as response:
                response.read()
        except URLError as exc:
            raise RuntimeError(f"Unable to send Discord notification to {url}") from exc
