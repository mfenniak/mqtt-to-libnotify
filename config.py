from dataclasses import dataclass

@dataclass
class NotifySendConfig:
    path: str

@dataclass
class MqttConfig:
    hostname: str
    port: int
    username: str
    password: str

@dataclass
class Config:
    notifysend: NotifySendConfig
    icon_path: str
    mqtt: MqttConfig
