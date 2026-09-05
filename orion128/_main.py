#   Orion-128 home computer emulator.
#   https://github.com/kosarev/orion128
#
#   Copyright (C) 2026 Ivan Kosarev.
#   mail@ivankosarev.com
#
#   Published under the MIT license.

import sys
import time
from pathlib import Path

from ._display import Display
from ._machine import CPU_FREQUENCY, Orion128Machine

# The window is redrawn this many times a second, and the processor runs a
# matching slice of ticks between redraws, so it runs at about real speed.
FRAMES_PER_SECOND = 50

# The bundled default ROMs live next to this module.
_PACKAGE = Path(__file__).parent


def _take_path(args: list[str], option: str) -> str:
    if not args:
        sys.exit(f'orion128: {option} needs a path')
    return args.pop(0)


def _parse_args(args: list[str]) -> tuple[Path, Path, list[Path]]:
    '''Read the leading options -- '--monitor PATH' and '--romdisk PATH',
    each defaulting to the bundled ROM -- followed by any number of ORDOS
    files (.ORD or .BRU) to preload onto the RAM-disk (drive B:).'''
    monitor = _PACKAGE / 'ms7007.rom'
    romdisk = _PACKAGE / 'disk.rom'
    while args and args[0].startswith('--'):
        option = args.pop(0)
        if option == '--monitor':
            monitor = Path(_take_path(args, option))
        elif option == '--romdisk':
            romdisk = Path(_take_path(args, option))
        else:
            sys.exit(f'orion128: unknown option: {option}')
    files = [Path(arg) for arg in args]
    return monitor, romdisk, files


def main() -> None:
    '''The orion128 command-line entry point.

    It runs the machine and shows its screen until the window is closed. By
    default it boots the bundled Monitor and ORDOS ROM-disk; '--monitor
    PATH' and '--romdisk PATH' replace them. Any further arguments are ORDOS
    files (.ORD or .BRU) preloaded onto the RAM-disk (drive B:).
    '''
    monitor, romdisk, files = _parse_args(sys.argv[1:])

    machine = Orion128Machine()
    machine.load_monitor(monitor.read_bytes())
    machine.load_romdisk(romdisk.read_bytes())
    if files:
        machine.load_ram_disk([path.read_bytes() for path in files])

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
