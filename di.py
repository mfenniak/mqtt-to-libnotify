from config import Config
from data.door import DoorDataResolver
from mainservice import MainService
from mqtt import MqttConfig, MqttServer
from notify.formatter import DoorStatusNotificationFormatter
from notify.notifysend import NotifySend
import asyncio

class Container:
    def __init__(self, config: Config):
        garage_door_status = DoorDataResolver(
            topic="homeassistant/output/door/garage_door"
        )

        mqtt_config = MqttConfig(
            hostname=config.mqtt.hostname,
            port=config.mqtt.port,
            username=config.mqtt.username,
            password=config.mqtt.password,
            discovery_prefix=None,
            discovery_node_id=None,
            discovery_object_id=None,
        )

        notifysend = NotifySend(
            notify_send_cmd=config.notifysend.path,
        )

        door_status_notification_formatter = DoorStatusNotificationFormatter(
            icon_path=config.icon_path,
            notification_source=garage_door_status,
            notification_sink=notifysend,
        )

        shutdown_event = asyncio.Event()

        mqtt_server = MqttServer(
            config=mqtt_config,
            shutdown_event=shutdown_event,
            other_receivers=[
                garage_door_status,
            ],
        )

        self.main_service = MainService(
            shutdown_event=shutdown_event,
            services=[
                mqtt_server,
                door_status_notification_formatter,
            ]
        )
