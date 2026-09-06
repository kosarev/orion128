#   Orion-128 home computer emulator.
#   https://github.com/kosarev/orion128
#
#   Copyright (C) 2026 Ivan Kosarev.
#   mail@ivankosarev.com
#
#   Published under the MIT license.

from pathlib import Path

import pytest

from orion128._disk import SYSTEM_TRACKS_SIZE, DiskImage
from orion128._main import run_command


def test_file_commands(tmp_path: Path,
                       capsys: pytest.CaptureFixture[str]) -> None:
    image = tmp_path / 'disk.odi'
    run_command('format', [str(image)])

    one = tmp_path / 'one.txt'
    one.write_bytes(b'one')
    two = tmp_path / 'two.com'
    two.write_bytes(b'two')
    run_command('save', [str(image), str(one)])
    run_command('save', [str(image), str(two), '--user', '1'])

    run_command('dir', [str(image)])
    assert capsys.readouterr().out == 'ONE.TXT\n'
    run_command('dir', [str(image), '--user', '1'])
    assert capsys.readouterr().out == 'TWO.COM\n'

    # Saving again replaces the file rather than failing.
    one.write_bytes(b'again')
    run_command('save', [str(image), str(one)])
    disk = DiskImage(image.read_bytes())
    assert disk.files.read('one.txt').startswith(b'again')

    run_command('era', [str(image), 'one.txt'])
    run_command('dir', [str(image)])
    assert capsys.readouterr().out == ''

    with pytest.raises(SystemExit, match='already exists'):
        run_command('format', [str(image)])
    with pytest.raises(SystemExit, match='too small'):
        run_command('dir', [str(one)])
    with pytest.raises(SystemExit, match='--user needs a number'):
        run_command('dir', [str(image), '--user'])


def test_sysgen(tmp_path: Path) -> None:
    source = tmp_path / 'source.odi'
    run_command('format', [str(source)])
    system = bytes(range(256)) * (SYSTEM_TRACKS_SIZE // 256)
    disk = DiskImage(source.read_bytes())
    disk.system_tracks = system
    source.write_bytes(bytes(disk))

    # The tracks extract to a plain file and install from it, leaving
    # the destination's files alone.
    tracks = tmp_path / 'system.bin'
    run_command('sysgen', [str(source), str(tracks)])
    assert tracks.read_bytes() == system

    destination = tmp_path / 'destination.odi'
    run_command('format', [str(destination), '--tracks', '82'])
    mine = tmp_path / 'mine.txt'
    mine.write_bytes(b'mine')
    run_command('save', [str(destination), str(mine)])
    run_command('sysgen', [str(tracks), str(destination)])
    disk = DiskImage(destination.read_bytes())
    assert disk.system_tracks == system
    assert disk.files.names() == ['MINE.TXT']

    # Disk to disk works too, and a plain file is not overwritten.
    run_command('sysgen', [str(source), str(destination)])
    with pytest.raises(SystemExit, match='already exists'):
        run_command('sysgen', [str(source), str(tracks)])
