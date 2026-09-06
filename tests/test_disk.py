#   Orion-128 home computer emulator.
#   https://github.com/kosarev/orion128
#
#   Copyright (C) 2026 Ivan Kosarev.
#   mail@ivankosarev.com
#
#   Published under the MIT license.

import pytest

from orion128._disk import (
    DEFAULT_TRACKS,
    DISK_FORMAT,
    SYSTEM_TRACKS_SIZE,
    DiskImage,
    blank_disk,
)
from orion128._floppy import TRACK_SIZE


def test_blank_disk_and_files() -> None:
    image = blank_disk()
    assert len(image) == DEFAULT_TRACKS * TRACK_SIZE

    # A fresh disk is empty, and files put on it come back through the
    # bytes of the image.
    disk = DiskImage(image)
    assert disk.files.names() == []
    disk.files.write('hello.txt', b'hello')

    disk = DiskImage(bytes(disk))
    assert disk.files.names() == ['HELLO.TXT']
    assert disk.files.read('hello.txt').startswith(b'hello')

    # The image beyond what the format describes is untouched.
    assert bytes(disk)[DISK_FORMAT.disk_size:] == image[DISK_FORMAT.disk_size:]

    # An image must cover what the format describes.
    with pytest.raises(ValueError, match='too small'):
        DiskImage(b'\xe5' * (40 * TRACK_SIZE))
    with pytest.raises(ValueError, match='too few'):
        blank_disk(tracks=40)


def test_system_tracks() -> None:
    system = bytes(range(256)) * (SYSTEM_TRACKS_SIZE // 256)
    disk = DiskImage(blank_disk(tracks=82))
    disk.system_tracks = system
    disk.files.write('keep.me', b'kept')

    # The system tracks and the files coexist in the image.
    disk = DiskImage(bytes(disk))
    assert disk.system_tracks == system
    assert disk.files.names() == ['KEEP.ME']

    with pytest.raises(ValueError, match='bytes, not 3'):
        disk.system_tracks = b'abc'
