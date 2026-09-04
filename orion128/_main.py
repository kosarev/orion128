#   Orion-128 home computer emulator.
#   https://github.com/kosarev/orion128
#
#   Copyright (C) 2026 Ivan Kosarev.
#   mail@ivankosarev.com
#
#   Published under the MIT license.

import time

import numpy as np

from ._display import Display
from ._machine import SCREEN_HEIGHT, SCREEN_WIDTH, VIDEO_BASE, Orion128Machine


def _draw_test_pattern(machine: Orion128Machine) -> None:
    '''Fill the video memory with a border and a diagonal.

    This is temporary. It gives the window something to show and confirms
    the screen orientation until the ROM runs and draws its own screen.
    '''
    pixels = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH), dtype=np.uint8)
    pixels[[0, -1], :] = 1
    pixels[:, [0, -1]] = 1
    diagonal = np.arange(min(SCREEN_HEIGHT, SCREEN_WIDTH))
    pixels[diagonal, diagonal] = 1

    # Pack the pixels back into the machine's column-major byte layout.
    columns = np.packbits(pixels, axis=1).T
    machine.set_memory_block(VIDEO_BASE, columns.reshape(-1).tobytes())


def main() -> None:
    '''The orion128 command-line entry point.

    It opens the screen window and shows the video memory until the window
    is closed. There is no ROM yet, so it draws a test pattern.
    '''
    machine = Orion128Machine()
    _draw_test_pattern(machine)

    display = Display()
    try:
        while not display.closed():
            display.update(machine.read_screen())
            time.sleep(0.02)
    finally:
        display.close()
