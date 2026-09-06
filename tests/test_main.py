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
from orion128._main import main, run_command


def test_help(capsys: pytest.CaptureFixture[str],
              monkeypatch: pytest.MonkeyPatch) -> None:
    for option in ('--help', '-h'):
        monkeypatch.setattr('sys.argv', ['orion128', option])
        main()
        out = capsys.readouterr().out
        assert out.startswith('Orion-128 home computer emulator.\nusage:')
        # Every disk image command has its usage line in the help.
        for command in ('dir', 'save', 'ren', 'era', 'format', 'sysgen'):
            assert f'orion128 {command} ' in out

    # A usage error prints just the command's usage line.
    with pytest.raises(SystemExit, match='^usage: orion128 dir IMAGE'):
        run_command('dir', [])

    # A file argument that is not there is reported, not a traceback.
    monkeypatch.setattr('sys.argv', ['orion128', 'nothere'])
    with pytest.raises(SystemExit, match='nothere: no such file'):
        main()


def test_file_commands(tmp_path: Path, capsys: pytest.CaptureFixture[str],
                       monkeypatch: pytest.MonkeyPatch) -> None:
    image = tmp_path / 'disk.odi'
    run_command('format', [str(image)])

    one = tmp_path / 'one.txt'
    one.write_bytes(b'one')
    two = tmp_path / 'two.com'
    two.write_bytes(b'two')
    run_command('save', [str(one), str(image)])
    run_command('save', [str(two), str(image), '--user', '1'])

    # The listing covers every user area by default, a line per file
    # with the user number, the name and the size in bytes.
    run_command('dir', [str(image)])
    assert capsys.readouterr().out == '0  ONE.TXT  128\n1  TWO.COM  128\n'
    run_command('dir', [str(image), '--user', '0'])
    assert capsys.readouterr().out == 'ONE.TXT  128\n'
    run_command('dir', [str(image), '--user', '1'])
    assert capsys.readouterr().out == 'TWO.COM  128\n'

    # Saving again replaces the file rather than failing.
    one.write_bytes(b'again')
    run_command('save', [str(one), str(image)])
    disk = DiskImage(image.read_bytes())
    assert disk.files.read('one.txt').startswith(b'again')

    # With the image first, the files come off the disk into the current
    # directory, and never over an existing host file.
    monkeypatch.chdir(tmp_path)
    two.unlink()
    run_command('save', [str(image), 'two.com', '--user', '1'])
    assert two.read_bytes().startswith(b'two')
    with pytest.raises(SystemExit, match='already exists'):
        run_command('save', [str(image), 'one.txt'])
    with pytest.raises(SystemExit, match='one end of save'):
        run_command('save', ['one.txt', 'two.com'])

    # Renaming takes CP/M's NEW=OLD form, within the user area.
    run_command('ren', [str(image), 'three.com=two.com', '--user', '1'])
    run_command('dir', [str(image), '--user', '1'])
    assert capsys.readouterr().out == 'THREE.COM  128\n'
    with pytest.raises(SystemExit, match='file not found'):
        run_command('ren', [str(image), 'four.com=two.com'])
    with pytest.raises(SystemExit, match='^usage: orion128 ren'):
        run_command('ren', [str(image), 'two.com', 'four.com'])

    run_command('era', [str(image), 'one.txt'])
    run_command('dir', [str(image), '--user', '0'])
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
    run_command('save', [str(mine), str(destination)])
    run_command('sysgen', [str(tracks), str(destination)])
    disk = DiskImage(destination.read_bytes())
    assert disk.system_tracks == system
    assert disk.files.names() == ['MINE.TXT']

    # Disk to disk works too, and a plain file is not overwritten.
    run_command('sysgen', [str(source), str(destination)])
    with pytest.raises(SystemExit, match='already exists'):
        run_command('sysgen', [str(source), str(tracks)])
