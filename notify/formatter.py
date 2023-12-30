from .notification_source import NotificationSource
from .notification_sink import NotificationSink
from .notifysend import DesktopNotification
from data import DoorInformation, DoorStatus
from service import Service

class DoorStatusNotificationFormatter(Service, NotificationSink[DoorInformation]):
    def __init__(self, icon_path: str, notification_source: NotificationSource[DoorInformation], notification_sink: NotificationSink[DesktopNotification]):
        self.icon_path = icon_path
        self.notification_source = notification_source
        self.notification_sink = notification_sink

    async def start(self) -> None:
        self.notification_source.subscribe(self)

    async def notify(self, door_information: DoorInformation) -> None:
        if door_information.status == DoorStatus.OPEN:
            text = "Garage Opening"
        else:
            text = "Garage Closing"

        await self.notification_sink.notify(
            DesktopNotification(
                summary="Garage Status",
                body=text,
                app_name="mqtt-to-libnotify",
                icon=f"{self.icon_path}garage.png",
            )
        )
