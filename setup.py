#!/usr/bin/env python

from distutils.core import setup
import os

setup(
    name="mqtt_to_libnotify",
    py_modules=[
        'data/__init__',
        'data/door',
        'di',
        'mqtt',
        'mainservice',
        'service',
    ],
    scripts=['main.py'],
    data_files=[
        ("icons", [f"icons/{x}" for x in os.listdir("icons")]),
    ]
)
