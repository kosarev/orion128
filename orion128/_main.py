#   Orion-128 home computer emulator.
#   https://github.com/kosarev/orion128
#
#   Copyright (C) 2026 Ivan Kosarev.
#   mail@ivankosarev.com
#
#   Published under the MIT license.

import sys
import time

import numpy as np

from ._display import Display
from ._machine import (
    CPU_FREQUENCY,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    VIDEO_BASE,
    Orion128Machine,
)

# The window is redrawn this many times a second, and the processor runs a
# matching slice of ticks between redraws, so it runs at about real speed.
FRAMES_PER_SECOND = 50


def _draw_test_pattern(machine: Orion128Machine) -> None:
    '''Fill the video memory with a border and a diagonal.

    This gives the window something to show when no Monitor ROM is given,
    and confirms the screen orientation.
    '''
    pixels = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH), dtype=np.uint8)
    pixels[[0, -1], :] = 1
    pixels[:, [0, -1]] = 1
    diagonal = np.arange(min(SCREEN_HEIGHT, SCREEN_WIDTH))
    pixels[diagonal, diagonal] = 1

    # Pack the pixels back into the machine's column-major byte layout.
    columns = np.packbits(pixels, axis=1).T
    machine.set_memory_block(VIDEO_BASE, columns.reshape(-1).tobytes())


def _take_path(args: list[str], option: str) -> str:
    if not args:
        sys.exit(f'orion128: {option} needs a path')
    return args.pop(0)


def _parse_args(args: list[str]) -> tuple[str | None, str | None, list[str]]:
    '''Read the leading options: '--monitor PATH', '--romdisk PATH' and
    '--ord PATH' (repeatable, each preloaded onto the RAM-disk).'''
    monitor = None
    romdisk = None
    ords = []
    while args and args[0].startswith('--'):
        option = args.pop(0)
        if option == '--monitor':
            monitor = _take_path(args, option)
        elif option == '--romdisk':
            romdisk = _take_path(args, option)
        elif option == '--ord':
            ords.append(_take_path(args, option))
        else:
            sys.exit(f'orion128: unknown option: {option}')
    return monitor, romdisk, ords


def _read_file(path: str) -> bytes:
    with open(path, 'rb') as f:
        return f.read()


def main() -> None:
    '''The orion128 command-line entry point.

    With '--monitor PATH' it loads that Monitor ROM and runs the machine,
    showing the screen until the window is closed. '--romdisk PATH' attaches
    a ROM-disk, which the Monitor boots into (ORDOS). '--ord PATH' preloads
    an ORDOS file onto the RAM-disk (drive B:); repeat it for several files.
    With no ROM it just shows a test pattern.
    '''
    monitor, romdisk, ords = _parse_args(sys.argv[1:])

    machine = Orion128Machine()
    if monitor is not None:
        machine.load_monitor(_read_file(monitor))
        if romdisk is not None:
            machine.load_romdisk(_read_file(romdisk))
        if ords:
            machine.load_ram_disk([_read_file(path) for path in ords])
    else:
        _draw_test_pattern(machine)

    ticks_per_frame = CPU_FREQUENCY // FRAMES_PER_SECOND
    display = Display()
    try:
        while not display.closed():
            if monitor is not None:
                if display.take_reset():
                    machine.reset()
                machine.set_keys(display.pressed_keys())
                machine.ticks_to_stop = ticks_per_frame
                machine.run()
            display.update(machine.render())
            time.sleep(1 / FRAMES_PER_SECOND)
    finally:
        display.close()
