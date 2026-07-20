from typing import Protocol, runtime_checkable
from core.events.base import Event

@runtime_checkable
class EventHandler(Protocol):
    """Protocol for classes that handle events."""
    async def __call__(self, event: Event) -> None:
        ...

class EventSubscriber(Protocol):
    """Protocol for classes that subscribe to events."""
    def setup_subscriptions(self) -> None:
        """Register handlers with the event bus."""
        ...

class EventPublisher(Protocol):
    """Protocol for classes that publish events."""
    async def publish_event(self, event: Event) -> None:
        ...
