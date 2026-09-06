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

import cpm80

from ._disk import DEFAULT_TRACKS, DiskImage, blank_disk
from ._display import Display
from ._floppy import is_disk_image
from ._keyboard import MS7007, RK86
from ._machine import CPU_FREQUENCY, Orion128Machine, Orion128Z80Machine
from ._ordos import ORDOSFile

# The window is redrawn this many times a second, and the processor runs a
# matching slice of ticks between redraws, so it runs at about real speed.
FRAMES_PER_SECOND = 50

# The bundled default ROMs live next to this module.
_PACKAGE = Path(__file__).parent


def _take_path(args: list[str], option: str) -> Path:
    if not args:
        sys.exit(f'orion128: {option} needs a path')
    return Path(args.pop(0))


def _parse_args(
        args: list[str]
        ) -> tuple[bool, bool, Path | None, Path | None, list[Path]]:
    '''Read the leading options and the file arguments.

    The options are '--rk86' (the RK-86 keyboard machine, with its Monitor
    and keyboard layout), '--z80' (run on the Z80 core, for software that
    uses Z80 instructions), and '--monitor PATH' and '--romdisk PATH' (each
    replacing the bundled default). The remaining arguments are files, each
    sorted by name and size: a floppy image goes in the drive, an ORDOS
    file (.ORD or .BRU) is preloaded onto the RAM-disk (drive B:). A missing
    monitor or ROM-disk is returned as None for the caller to default.
    '''
    rk86 = False
    z80 = False
    monitor = None
    romdisk = None
    while args and args[0].startswith('--'):
        option = args.pop(0)
        if option == '--rk86':
            rk86 = True
        elif option == '--z80':
            z80 = True
        elif option == '--monitor':
            monitor = _take_path(args, option)
        elif option == '--romdisk':
            romdisk = _take_path(args, option)
        else:
            sys.exit(f'orion128: unknown option: {option}')
    files = [Path(arg) for arg in args]
    return rk86, z80, monitor, romdisk, files


def _take_user(args: list[str]) -> int:
    '''Remove a '--user N' option from the arguments and return N.'''
    if '--user' not in args:
        return 0
    at = args.index('--user')
    del args[at]
    if at == len(args):
        raise ValueError('--user needs a number')
    return int(args.pop(at))


def _read_disk(path: Path) -> DiskImage:
    try:
        return DiskImage(path.read_bytes())
    except ValueError as e:
        raise ValueError(f'{path}: {e}')


def _write_new_file(path: Path, data: bytes) -> None:
    if path.exists():
        raise ValueError(f'{path}: already exists')
    path.write_bytes(data)


def _dir(args: list[str]) -> None:
    user = _take_user(args)
    if len(args) != 1:
        raise ValueError('usage: orion128 dir IMAGE [--user N]')
    for name in _read_disk(Path(args[0])).files.names(user):
        print(name)


def _era(args: list[str]) -> None:
    user = _take_user(args)
    if len(args) < 2:
        raise ValueError('usage: orion128 era IMAGE NAME... [--user N]')
    path = Path(args[0])
    disk = _read_disk(path)
    for name in args[1:]:
        disk.files.delete(name, user)
    path.write_bytes(bytes(disk))


def _save(args: list[str]) -> None:
    user = _take_user(args)
    if len(args) < 2:
        raise ValueError('usage: orion128 save IMAGE FILE... [--user N]')
    path = Path(args[0])
    disk = _read_disk(path)
    present = {name.lower() for name in disk.files.names(user)}
    for file in map(Path, args[1:]):
        # A file already there under the name is replaced.
        if file.name.lower() in present:
            disk.files.delete(file.name, user)
        disk.files.write(file.name, file.read_bytes(), user)
    path.write_bytes(bytes(disk))


def _format(args: list[str]) -> None:
    tracks = DEFAULT_TRACKS
    if '--tracks' in args:
        at = args.index('--tracks')
        del args[at]
        if at == len(args):
            raise ValueError('--tracks needs a number')
        tracks = int(args.pop(at))
    if len(args) != 1:
        raise ValueError('usage: orion128 format IMAGE [--tracks N]')
    _write_new_file(Path(args[0]), blank_disk(tracks))


def _sysgen(args: list[str]) -> None:
    '''Copy the system tracks. Either end is an image or a plain file
    holding just the tracks, so they can be extracted and installed.'''
    if len(args) != 2:
        raise ValueError('usage: orion128 sysgen SOURCE DESTINATION')
    source, destination = Path(args[0]), Path(args[1])

    if is_disk_image(source.stat().st_size):
        tracks = _read_disk(source).system_tracks
    else:
        tracks = source.read_bytes()

    if destination.exists() and is_disk_image(destination.stat().st_size):
        disk = _read_disk(destination)
        disk.system_tracks = tracks
        destination.write_bytes(bytes(disk))
    else:
        _write_new_file(destination, tracks)


# The disk image commands, named after their CP/M counterparts. They work
# on an image from the host, without the machine.
_COMMANDS = {'dir': _dir, 'era': _era, 'save': _save, 'format': _format,
             'sysgen': _sysgen}


def run_command(command: str, args: list[str]) -> None:
    '''Run a disk image command on its arguments, exiting with a message
    on any error.'''
    try:
        _COMMANDS[command](list(args))
    except (cpm80.Error, ValueError, OSError) as e:
        sys.exit(f'orion128: {e}')


def main() -> None:
    '''The orion128 command-line entry point.

    It runs the machine and shows its screen until the window is closed. By
    default it boots the bundled MS7007 Monitor and ORDOS ROM-disk. '--rk86'
    selects the RK-86 keyboard machine instead, with its own Monitor and
    keyboard layout. '--z80' runs on the Z80 core, for software that uses
    Z80 instructions. '--monitor PATH' and '--romdisk PATH' replace the
    bundled ROMs. Any further arguments are files: a floppy image goes in
    the drive, an ORDOS file (.ORD or .BRU) is preloaded onto the RAM-disk
    (drive B:).

    Given a disk image command as its first argument (dir, era, save,
    format or sysgen), it works on the image from the host instead.
    '''
    args = sys.argv[1:]

    if args and args[0] in _COMMANDS:
        run_command(args[0], args[1:])
        return

    rk86, z80, monitor, romdisk, files = _parse_args(args)

    if monitor is None:
        monitor = _PACKAGE / ('m2rk86.rom' if rk86 else 'ms7007.rom')
    if romdisk is None:
        romdisk = _PACKAGE / 'disk.rom'

    # Sort the file arguments: a floppy image (recognised by its size) goes
    # in a drive; anything else is an ORDOS file for the RAM-disk. A
    # .ORD/.BRU name is always an ORDOS file, never a disk. The disk images
    # fill the drives in the order given (A, B, C, D).
    disks = []
    ordos_paths = []
    for path in files:
        if path.suffix.lower() in ('.ord', '.bru'):
            ordos_paths.append(path)
        elif is_disk_image(path.stat().st_size):
            disks.append(path)
        else:
            sys.exit(f'orion128: {path}: not an ORDOS file or a disk image')
    if len(disks) > 4:
        sys.exit('orion128: at most four floppy drives are supported')

    ordos_files = []
    for path in ordos_paths:
        try:
            ordos_files.append(ORDOSFile.parse(path.read_bytes()))
        except ValueError as e:
            sys.exit(f'orion128: {path}: {e}')

    machine = Orion128Z80Machine() if z80 else Orion128Machine()
    machine.load_monitor(monitor.read_bytes())
    machine.load_romdisk(romdisk.read_bytes())
    machine.mount_disks([path.read_bytes() for path in disks])
    if ordos_files:
        machine.load_ram_disk(ordos_files)

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
