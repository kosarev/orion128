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
from ._floppy import is_disk_image
from ._keyboard import MS7007, RK86
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


def _parse_args(
        args: list[str]) -> tuple[bool, Path | None, Path | None, list[Path]]:
    '''Read the leading options and the file arguments.

    The options are '--rk86' (the RK-86 keyboard machine, with its Monitor
    and keyboard layout), '--monitor PATH' and '--romdisk PATH' (each
    replacing the bundled default). The remaining arguments are files, each
    sorted by name and size: a floppy image goes in the drive, an ORDOS
    file (.ORD or .BRU) is preloaded onto the RAM-disk (drive B:). A missing
    monitor or ROM-disk is returned as None for the caller to default.
    '''
    rk86 = False
    monitor = None
    romdisk = None
    while args and args[0].startswith('--'):
        option = args.pop(0)
        if option == '--rk86':
            rk86 = True
        elif option == '--monitor':
            monitor = Path(_take_path(args, option))
        elif option == '--romdisk':
            romdisk = Path(_take_path(args, option))
        else:
            sys.exit(f'orion128: unknown option: {option}')
    files = [Path(arg) for arg in args]
    return rk86, monitor, romdisk, files


def main() -> None:
    '''The orion128 command-line entry point.

    It runs the machine and shows its screen until the window is closed. By
    default it boots the bundled MS7007 Monitor and ORDOS ROM-disk. '--rk86'
    selects the RK-86 keyboard machine instead, with its own Monitor and
    keyboard layout. '--monitor PATH' and '--romdisk PATH' replace the
    bundled ROMs. Any further arguments are files: a floppy image goes in
    the drive, an ORDOS file (.ORD or .BRU) is preloaded onto the RAM-disk
    (drive B:).
    '''
    rk86, monitor, romdisk, files = _parse_args(sys.argv[1:])

    if monitor is None:
        monitor = _PACKAGE / ('m2rk86.rom' if rk86 else 'ms7007.rom')
    if romdisk is None:
        romdisk = _PACKAGE / 'disk.rom'

    # Sort the file arguments: a floppy image (recognised by its size) goes
    # in the drive; anything else is an ORDOS file for the RAM-disk. A
    # .ORD/.BRU name is always an ORDOS file, never a disk.
    disks = []
    ords = []
    for path in files:
        if path.suffix.lower() in ('.ord', '.bru'):
            ords.append(path)
        elif is_disk_image(path.stat().st_size):
            disks.append(path)
        else:
            sys.exit(f'orion128: {path}: not an ORDOS file or a disk image')
    if len(disks) > 1:
        sys.exit('orion128: only one floppy drive is supported')

    machine = Orion128Machine()
    machine.load_monitor(monitor.read_bytes())
    machine.load_romdisk(romdisk.read_bytes())
    if disks:
        machine.mount_disk(disks[0].read_bytes())
    if ords:
        machine.load_ram_disk([path.read_bytes() for path in ords])

    ticks_per_frame = CPU_FREQUENCY // FRAMES_PER_SECOND
    display = Display(keyboard=RK86 if rk86 else MS7007)
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
