from data.door import DoorDataResolver
from dependency_injector import containers, providers
from mqtt import MqttConfig, MqttServer
from mainservice import MainService
from notify.notifysend import NotifySend
from notify.formatter import DoorStatusNotificationFormatter
import asyncio

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    garage_door_status = providers.Singleton(
        DoorDataResolver,
        topic="homeassistant/output/door/garage_door",
    )
    # garage_man_door_status = providers.Singleton(
    #     DoorDataResolver,
    #     topic="homeassistant/output/door/garage_man_door",
    # )
    # back_door_status = providers.Singleton(
    #     DoorDataResolver,
    #     topic="homeassistant/output/door/back_door",
    # )

    mqtt_config = providers.Singleton(
        MqttConfig,
        hostname=config.mqtt.hostname,
        port=config.mqtt.port,
        username=config.mqtt.username,
        password=config.mqtt.password,
        discovery_prefix=config.mqtt.discovery.prefix,
        discovery_node_id=config.mqtt.discovery.node_id,
        discovery_object_id=config.mqtt.discovery.object_id,
    )

    notifysend = providers.Singleton(
        NotifySend,
        notify_send_cmd=config.notifysend.path,
    )

    door_status_notification_formatter = providers.Singleton(
        DoorStatusNotificationFormatter,
        icon_path=config.icon_path,
        notification_source=garage_door_status,
        notification_sink=notifysend,
    )

    shutdown_event = providers.Singleton(asyncio.Event)

    mqtt_server = providers.Singleton(
        MqttServer,
        config=mqtt_config,
        shutdown_event=shutdown_event,
        other_receivers=providers.List(
            garage_door_status,
        ),
    )

    main_service = providers.Singleton(
        MainService,
        shutdown_event=shutdown_event,
        services=providers.List(
            mqtt_server,
            door_status_notification_formatter,
        )
    )
