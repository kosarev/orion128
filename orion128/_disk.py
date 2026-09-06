#   Orion-128 home computer emulator.
#   https://github.com/kosarev/orion128
#
#   Copyright (C) 2026 Ivan Kosarev.
#   mail@ivankosarev.com
#
#   Published under the MIT license.

'''The CP/M side of Orion floppy images.

Every Orion CP/M system seen (OS-DOS, ORION-DOS, CP/M 3) lays its disks
out the same way, so the format is fixed here.
'''

import cpm80

from ._floppy import SECTOR_SIZE, SECTORS_PER_TRACK, TRACK_SIZE

# The systems' choices, read off the disk parameter blocks in their own
# tracks. A CP/M track is one side of a physical track, counted in
# 128-byte records. Four of them (two cylinders, 20K) are reserved for the
# system; the blocks are 2K and the directory holds 128 entries. The
# systems count 389 blocks, one short of what an 80-track disk holds, and
# no more on an 82-track disk, so the rest is never used.
DISK_FORMAT = cpm80.DiskFormat(
    sectors_per_track=SECTORS_PER_TRACK * SECTOR_SIZE // cpm80.SECTOR_SIZE,
    num_reserved_tracks=4, block_size=2048, num_blocks=389,
    num_dir_entries=128)

SYSTEM_TRACKS_SIZE = DISK_FORMAT.reserved_size

DEFAULT_TRACKS = 80


class DiskImage(cpm80.DiskImage):
    '''An Orion floppy image as a CP/M disk image, with its file system.

    The format describes less than the image holds, so the rest is kept
    aside and comes back with the data in bytes(image).
    '''
    def __init__(self, image: bytes) -> None:
        if len(image) < DISK_FORMAT.disk_size:
            raise ValueError('too small for an Orion CP/M disk')
        super().__init__(DISK_FORMAT, data=image[:DISK_FORMAT.disk_size],
                         store_format=False)
        self.__rest = image[DISK_FORMAT.disk_size:]
        self.files = cpm80.FileSystem(self)

    @property
    def system_tracks(self) -> bytes:
        return bytes(self.data[:SYSTEM_TRACKS_SIZE])

    @system_tracks.setter
    def system_tracks(self, data: bytes) -> None:
        if len(data) != SYSTEM_TRACKS_SIZE:
            raise ValueError(f'system tracks are {SYSTEM_TRACKS_SIZE} '
                             f'bytes, not {len(data)}')
        self.data[:SYSTEM_TRACKS_SIZE] = data

    def __bytes__(self) -> bytes:
        return bytes(self.data) + self.__rest


def blank_disk(tracks: int = DEFAULT_TRACKS) -> bytes:
    '''A blank image: an empty directory and empty system tracks.'''
    image = bytearray(b'\xe5' * (tracks * TRACK_SIZE))
    if len(image) < DISK_FORMAT.disk_size:
        raise ValueError(f'{tracks} tracks are too few for an Orion CP/M '
                         f'disk')
    blank = cpm80.DiskImage(DISK_FORMAT, store_format=False)
    image[:DISK_FORMAT.disk_size] = blank.data
    return bytes(image)
