#   Orion-128 home computer emulator.
#   https://github.com/kosarev/orion128
#
#   Copyright (C) 2026 Ivan Kosarev.
#   mail@ivankosarev.com
#
#   Published under the MIT license.

from ._machine import (
    MONITOR_BASE,
    MONITOR_SIZE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    VIDEO_BASE,
    VIDEO_SIZE,
    Orion128Machine,
)
from ._main import main

__all__ = [
    'MONITOR_BASE',
    'MONITOR_SIZE',
    'SCREEN_HEIGHT',
    'SCREEN_WIDTH',
    'VIDEO_BASE',
    'VIDEO_SIZE',
    'Orion128Machine',
    'main',
]
