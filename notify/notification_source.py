from .notification_sink import NotificationSink
from typing import Any, TypeVar, Generic, List

T = TypeVar("T")

class NotificationSource(Generic[T]):
    def __init__(self) -> None:
        self.subscribers: List[NotificationSink[T]] = []

    def subscribe(self, subscriber: NotificationSink[T]) -> None:
        self.subscribers.append(subscriber)

    def unsubscribe(self, subscriber: NotificationSink[T]) -> None:
        self.subscribers.remove(subscriber)

    async def notify(self, arg: T) -> None:
        for subscriber in self.subscribers:
            await subscriber.notify(arg)
