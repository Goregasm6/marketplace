from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class AlertNotification:
    """Structured alert payload sent to notification providers."""

    title: str
    price: float
    estimated_value: float
    expected_profit: float
    flip_score: int
    confidence: float
    reasoning: str
    listing_url: str


class Notification:
    """Base interface for notification providers."""

    def send(self, alert: AlertNotification) -> None:
        raise NotImplementedError


class NotificationService:
    """Dispatches alerts to any pluggable notification providers."""

    def __init__(self, providers: Iterable[Notification] | None = None) -> None:
        self._providers = list(providers or [])

    def add_provider(self, provider: Notification) -> None:
        self._providers.append(provider)

    def send(self, alert: AlertNotification) -> None:
        for provider in self._providers:
            provider.send(alert)
