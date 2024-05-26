#!/usr/bin/env python

from distutils.core import setup
import os

setup(
    name="mqtt_to_libnotify",
    py_modules=[
        'config',
        'data/__init__',
        'data/door',
        'di',
        'mainservice',
        'mqtt',
        'notify/__init__',
        'notify/formatter',
        'notify/notification_sink',
        'notify/notification_source',
        'notify/notifysend',
        'service',
    ],
    scripts=['main.py'],
    data_files=[
        ("icons", [f"icons/{x}" for x in os.listdir("icons")]),
    ]
)
