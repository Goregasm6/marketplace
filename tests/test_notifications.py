from __future__ import annotations

from alerts.discord import DiscordNotification
from alerts.notifications import AlertNotification, Notification, NotificationService


class RecordingNotification(Notification):
    def __init__(self) -> None:
        self.sent: list[AlertNotification] = []

    def send(self, alert: AlertNotification) -> None:
        self.sent.append(alert)


def test_discord_notification_builds_expected_payload() -> None:
    sent_payloads: list[tuple[str, dict[str, object]]] = []

    def fake_post(url: str, payload: dict[str, object]) -> None:
        sent_payloads.append((url, payload))

    provider = DiscordNotification(
        webhook_url="https://discord.com/api/webhooks/123/abc",
        http_client=fake_post,
    )
    alert = AlertNotification(
        title="Vintage gaming console",
        price=149.0,
        estimated_value=260.0,
        expected_profit=111.0,
        flip_score=88,
        confidence=0.93,
        reasoning="Great demand and low competition",
        listing_url="https://example.com/listing/123",
    )

    provider.send(alert)

    assert len(sent_payloads) == 1
    url, payload = sent_payloads[0]
    assert url == "https://discord.com/api/webhooks/123/abc"
    assert payload["content"] == "New flip opportunity: Vintage gaming console"
    assert payload["embeds"][0]["title"] == "Vintage gaming console"
    assert payload["embeds"][0]["description"] == "Great demand and low competition"
    assert payload["embeds"][0]["fields"][0]["name"] == "Price"
    assert payload["embeds"][0]["fields"][0]["value"] == "$149.00"


def test_notification_service_dispatches_to_all_providers() -> None:
    first = RecordingNotification()
    second = RecordingNotification()
    service = NotificationService([first, second])
    alert = AlertNotification(
        title="Desk lamp",
        price=35.0,
        estimated_value=65.0,
        expected_profit=30.0,
        flip_score=72,
        confidence=0.79,
        reasoning="Solid margin",
        listing_url="https://example.com/listing/456",
    )

    service.send(alert)

    assert [provider.sent[0].title for provider in (first, second)] == ["Desk lamp", "Desk lamp"]
    assert first.sent[0].listing_url == "https://example.com/listing/456"
    assert second.sent[0].expected_profit == 30.0
