#   Orion-128 home computer emulator.
#   https://github.com/kosarev/orion128
#
#   Copyright (C) 2026 Ivan Kosarev.
#   mail@ivankosarev.com
#
#   Published under the MIT license.

import importlib.resources
import sys
import time

from ._display import Display
from ._machine import CPU_FREQUENCY, Orion128Machine

# The window is redrawn this many times a second, and the processor runs a
# matching slice of ticks between redraws, so it runs at about real speed.
FRAMES_PER_SECOND = 50


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


def _bundled(name: str) -> bytes:
    return (importlib.resources.files('orion128') / name).read_bytes()


def main() -> None:
    '''The orion128 command-line entry point.

    It runs the machine and shows its screen until the window is closed. By
    default it boots the bundled Monitor and ORDOS ROM-disk; '--monitor
    PATH' and '--romdisk PATH' replace them. '--ord PATH' preloads an ORDOS
    file (.ORD or .BRU) onto the RAM-disk (drive B:); repeat it for several.
    '''
    monitor, romdisk, ords = _parse_args(sys.argv[1:])

    machine = Orion128Machine()
    machine.load_monitor(_read_file(monitor) if monitor else
                         _bundled('ms7007.rom'))
    machine.load_romdisk(_read_file(romdisk) if romdisk else
                         _bundled('disk.rom'))
    if ords:
        machine.load_ram_disk([_read_file(path) for path in ords])

    ticks_per_frame = CPU_FREQUENCY // FRAMES_PER_SECOND
    display = Display()
    try:
        while not display.closed():
            if display.take_reset():
                machine.reset()
            machine.set_keys(display.pressed_keys())
            machine.ticks_to_stop = ticks_per_frame
            machine.run()
            display.update(machine.render())
            time.sleep(1 / FRAMES_PER_SECOND)
    finally:
        display.close()
