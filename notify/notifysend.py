import asyncio
import subprocess
import os.path
from typing import Optional
from .notification_sink import NotificationSink
from dataclasses import dataclass

@dataclass
class DesktopNotification:
    summary: str
    body: Optional[str] = None
    urgency: Optional[str] = None
    expire_time: Optional[int] = None
    app_name: Optional[str] = None
    icon: Optional[str] = None

class NotifySend(NotificationSink[DesktopNotification]):
    def __init__(self, notify_send_cmd: str) -> None:
        self.notify_send_cmd = notify_send_cmd

    async def notify(self, notification: DesktopNotification) -> None:
        print("NotifySend.notify", notification)

        cmd = [self.notify_send_cmd]

        if notification.urgency:
            cmd.extend(['-u', notification.urgency])
        if notification.expire_time is not None:
            cmd.extend(['-t', str(notification.expire_time)])
        if notification.app_name:
            cmd.extend(['-a', notification.app_name])
        if notification.icon:
            cmd.extend(['-i', os.path.abspath(notification.icon)])

        cmd.append(notification.summary)
        if notification.body:
            cmd.append(notification.body)

        process = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f'notify-send command failed: {stderr.decode()}')
