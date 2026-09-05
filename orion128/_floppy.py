#   Orion-128 home computer emulator.
#   https://github.com/kosarev/orion128
#
#   Copyright (C) 2026 Ivan Kosarev.
#   mail@ivankosarev.com
#
#   Published under the MIT license.

'''The KR1818VG93 floppy disk controller, a WD1793 clone.

The controller is driven by programmed I/O through the F700 expansion:
four registers -- command/status, track, sector, data -- and a control
register that selects the drive and side (Radio 1993/05-06). A program
issues a command, then reads or writes the data register a byte at a time
while the status shows a data request, until the busy bit clears.

Only what the Orion software needs is emulated: positioning the head
(restore, seek, step) and reading whole sectors. Writing is to follow.
'''

# WD1793 status bits.
_BUSY = 0x01
_DRQ = 0x02
_NOT_FOUND = 0x10
_NOT_READY = 0x80

# The Orion floppies hold two sides of five 1024-byte sectors per track,
# the sectors numbered from one. The track count follows from the image
# size (80 or 82).
SIDES = 2
SECTORS_PER_TRACK = 5
SECTOR_SIZE = 1024
TRACK_SIZE = SIDES * SECTORS_PER_TRACK * SECTOR_SIZE


def is_disk_image(size: int) -> bool:
    '''Whether a file of this size is a floppy image: a whole number of
    tracks, and enough of them to be a real disk rather than an ORDOS
    file.'''
    return size % TRACK_SIZE == 0 and size // TRACK_SIZE >= 40


# The control register's side-select bit. Provisional, to be confirmed
# against the disk test: BOOT$ writes 0x10 and 0x50, so the 0x40 bit is
# the one that changes and reads as the side.
_SIDE_BIT = 0x40


class FDC:
    '''A single floppy drive behind a WD1793 controller.'''

    def __init__(self) -> None:
        self.__image: bytearray | None = None
        self.__tracks = 0
        self.__status = _NOT_READY
        self.__track = 0
        self.__sector = 1
        self.__data = 0
        self.__control = 0
        # The sector being transferred, and how far through it we are.
        self.__buffer = bytearray()
        self.__index = 0

    def mount(self, image: bytes) -> None:
        '''Put a disk image in the drive.'''
        self.__image = bytearray(image)
        self.__tracks = len(image) // (SIDES * SECTORS_PER_TRACK * SECTOR_SIZE)
        self.__status = 0

    def __offset(self) -> int | None:
        '''The image offset of the current track, side and sector, or None
        if there is no such sector.'''
        side = 1 if self.__control & _SIDE_BIT else 0
        if (self.__image is None or self.__track >= self.__tracks
                or not 1 <= self.__sector <= SECTORS_PER_TRACK):
            return None
        row = (self.__track * SIDES + side) * SECTORS_PER_TRACK
        return (row + self.__sector - 1) * SECTOR_SIZE

    def write_command(self, value: int) -> None:
        '''Handle a command written to the command register.'''
        if self.__image is None:
            self.__status = _NOT_READY
            return

        top = value & 0xf0
        # Type I positions the head and completes at once.
        if value < 0x80:
            if top == 0x00:                # restore
                self.__track = 0
            elif top == 0x10:              # seek to the track in the data reg
                self.__track = self.__data
            elif top in (0x40, 0x50):      # step in
                self.__track += 1
            elif top in (0x60, 0x70):      # step out
                self.__track = max(0, self.__track - 1)
            self.__status = 0
        # Read Sector: load the sector and request its bytes.
        elif value < 0xa0:
            offset = self.__offset()
            if offset is None:
                self.__status = _NOT_FOUND
                return
            assert self.__image is not None
            self.__buffer = self.__image[offset:offset + SECTOR_SIZE]
            self.__index = 0
            self.__status = _BUSY | _DRQ
        # Force Interrupt ends any operation.
        elif top == 0xd0:
            self.__buffer = bytearray()
            self.__index = 0
            self.__status = 0

    def write_track(self, value: int) -> None:
        self.__track = value

    def write_sector(self, value: int) -> None:
        self.__sector = value

    def write_data(self, value: int) -> None:
        self.__data = value

    def write_control(self, value: int) -> None:
        self.__control = value

    def read_status(self) -> int:
        return self.__status

    def read_request(self) -> int:
        # The request register reflects the data-request line.
        return self.__status & _DRQ

    def read_data(self) -> int:
        '''Return the next byte of the sector being read, dropping the
        request and the busy bit once the sector is spent.'''
        if self.__index >= len(self.__buffer):
            return 0
        value = self.__buffer[self.__index]
        self.__index += 1
        if self.__index >= len(self.__buffer):
            self.__status = 0
        return value
