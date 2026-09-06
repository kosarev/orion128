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
from ._keyboard import MS7007Keyboard, RK86Keyboard
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


class _UsageError(Exception):
    '''A command called with the wrong arguments. The message is the
    usage text, printed as it is.'''


# The usage lines, one entry per disk image command, shared by the
# command's usage error and the help text.
_USAGE = {
    'dir': ['orion128 dir IMAGE [--user N]'],
    'save': ['orion128 save FILE... IMAGE [--user N]',
             'orion128 save IMAGE NAME... [--user N]'],
    'ren': ['orion128 ren IMAGE NEW=OLD [--user N]'],
    'era': ['orion128 era IMAGE NAME... [--user N]'],
    'format': ['orion128 format IMAGE [--tracks N]'],
    'sysgen': ['orion128 sysgen SOURCE_IMAGE DESTINATION_IMAGE',
               'orion128 sysgen IMAGE FILE',
               'orion128 sysgen FILE IMAGE'],
}


def _usage(command: str) -> _UsageError:
    return _UsageError('usage: ' + '\n       '.join(_USAGE[command]))


_HELP = '\n'.join([
    'Orion-128 home computer emulator.',
    ('usage: orion128 [--rk86] [--z80] [--monitor PATH] [--romdisk PATH] '
     '[FILE...]'),
    '       orion128 --help',
    *(f'       {line}' for lines in _USAGE.values() for line in lines),
    '',
    'Runs the machine and shows its screen until the window is closed. F12',
    'is the RESET button, F10 closes the emulator.',
    '  --rk86          The RK-86 keyboard machine, with its own Monitor and',
    '                  keyboard layout.',
    '  --z80           Run on the Z80 core, for software that uses Z80',
    '                  instructions.',
    '  --monitor PATH  Replace the bundled Monitor ROM.',
    '  --romdisk PATH  Replace the bundled ORDOS ROM-disk.',
    '  FILE            A floppy image goes in the next drive (A: to D:). An',
    '                  ORDOS file (.ORD or .BRU) is preloaded onto the',
    '                  RAM-disk (drive B:).',
    '',
    'The disk image commands work on an image from the host, without the',
    'machine.',
    '  dir     List the files: user area, name and size in bytes. With',
    "          --user, one user area's, without the user column.",
    '  save    Copy host files onto the disk, or files off the disk into',
    '          the current directory. Files on the disk are replaced, files',
    '          on the host never overwritten.',
    '  ren     Rename a file, NEW=OLD as CP/M has it.',
    '  era     Delete files.',
    '  format  Make a blank disk of 80 tracks, or of N.',
    '  sysgen  Copy the system tracks from one disk to another, extract',
    '          them to a plain file, or install them from one.',
])


def _take_user(args: list[str]) -> int | None:
    '''Remove a '--user N' option from the arguments and return N, or
    None when there is none.'''
    if '--user' not in args:
        return None
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


def _is_disk_image_file(path: Path) -> bool:
    return path.is_file() and is_disk_image(path.stat().st_size)


def _dir(args: list[str]) -> None:
    '''List the files of every user area, a line per file with the user
    number, the name and the size, so a file in another user area is
    never overlooked and a script can pick lines apart. With a user
    given, the user number is left out.'''
    user = _take_user(args)
    if len(args) != 1:
        raise _usage('dir')
    for entry in _read_disk(Path(args[0])).files.entries(user):
        columns = [entry.name, str(entry.size)]
        if user is None:
            columns.insert(0, str(entry.user))
        print('  '.join(columns))


def _ren(args: list[str]) -> None:
    '''Rename a file, in CP/M's own NEW=OLD form.'''
    user = _take_user(args) or 0
    if len(args) != 2 or '=' not in args[1]:
        raise _usage('ren')
    path = Path(args[0])
    disk = _read_disk(path)
    new, _, old = args[1].partition('=')
    disk.files.rename(old, new, user)
    path.write_bytes(bytes(disk))


def _era(args: list[str]) -> None:
    user = _take_user(args) or 0
    if len(args) < 2:
        raise _usage('era')
    path = Path(args[0])
    disk = _read_disk(path)
    for name in args[1:]:
        disk.files.delete(name, user)
    path.write_bytes(bytes(disk))


def _save(args: list[str]) -> None:
    '''Copy files onto the disk image or off it, source first as with
    cp: the image last is the destination, the image first the source,
    with the current directory as the destination.'''
    user = _take_user(args) or 0
    if len(args) < 2:
        raise _usage('save')
    first, last = Path(args[0]), Path(args[-1])

    if _is_disk_image_file(last) and not _is_disk_image_file(first):
        disk = _read_disk(last)
        present = {name.lower() for name in disk.files.names(user)}
        for file in map(Path, args[:-1]):
            # A file already on the disk under the name is replaced.
            if file.name.lower() in present:
                disk.files.delete(file.name, user)
            disk.files.write(file.name, file.read_bytes(), user)
        last.write_bytes(bytes(disk))
    elif _is_disk_image_file(first) and not _is_disk_image_file(last):
        disk = _read_disk(first)
        for name in args[1:]:
            _write_new_file(Path(name), disk.files.read(name, user))
    else:
        raise ValueError('one end of save must be the disk image')


def _format(args: list[str]) -> None:
    tracks = DEFAULT_TRACKS
    if '--tracks' in args:
        at = args.index('--tracks')
        del args[at]
        if at == len(args):
            raise ValueError('--tracks needs a number')
        tracks = int(args.pop(at))
    if len(args) != 1:
        raise _usage('format')
    _write_new_file(Path(args[0]), blank_disk(tracks))


def _sysgen(args: list[str]) -> None:
    '''Copy the system tracks. Either end is an image or a plain file
    holding just the tracks, so they can be extracted and installed.'''
    if len(args) != 2:
        raise _usage('sysgen')
    source, destination = Path(args[0]), Path(args[1])

    if _is_disk_image_file(source):
        tracks = _read_disk(source).system_tracks
    else:
        tracks = source.read_bytes()

    if _is_disk_image_file(destination):
        disk = _read_disk(destination)
        disk.system_tracks = tracks
        destination.write_bytes(bytes(disk))
    else:
        _write_new_file(destination, tracks)


# The disk image commands, named after their CP/M counterparts. They work
# on an image from the host, without the machine.
_COMMANDS = {'dir': _dir, 'save': _save, 'ren': _ren, 'era': _era,
             'format': _format, 'sysgen': _sysgen}


def run_command(command: str, args: list[str]) -> None:
    '''Run a disk image command on its arguments, exiting with a message
    on any error.'''
    try:
        _COMMANDS[command](list(args))
    except _UsageError as e:
        sys.exit(str(e))
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

    if args and args[0] in ('--help', '-h'):
        print(_HELP)
        return

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
        if not path.is_file():
            sys.exit(f'orion128: {path}: no such file')
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
    try:
        machine.load_monitor(monitor.read_bytes())
        machine.load_romdisk(romdisk.read_bytes())
        machine.mount_disks([path.read_bytes() for path in disks])
    except OSError as e:
        sys.exit(f'orion128: {e.filename}: {e.strerror}')
    if ordos_files:
        machine.load_ram_disk(ordos_files)

    ticks_per_frame = CPU_FREQUENCY // FRAMES_PER_SECOND
    display = Display(keyboard=RK86Keyboard() if rk86 else MS7007Keyboard())
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
