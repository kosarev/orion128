#   Orion-128 home computer emulator.
#   https://github.com/kosarev/orion128
#
#   Copyright (C) 2026 Ivan Kosarev.
#   mail@ivankosarev.com
#
#   Published under the MIT license.

import numpy as np
import numpy.typing as npt
import z80

# The Orion-128 screen is a bitmap of this size.
SCREEN_WIDTH = 384
SCREEN_HEIGHT = 256

# The screen is a bitmap in the processor's address space. Each byte holds
# eight horizontal pixels, the most significant bit leftmost. The bytes run
# down a column of the screen before stepping to the next column to the
# right, so the byte for pixel (x, y) is at
# VIDEO_BASE + (x // 8) * SCREEN_HEIGHT + y.
# The base address and this layout are provisional until confirmed against
# the ROM and the disk images.
VIDEO_BASE = 0xc000
VIDEO_SIZE = (SCREEN_WIDTH // 8) * SCREEN_HEIGHT

# The 2K Monitor ROM sits at the top of memory. The i8080 resets to
# address 0, but on the Orion the reset makes the Monitor run first, and
# its first byte is a jump into itself. So starting the processor at
# MONITOR_BASE reproduces the boot without emulating the reset ROM overlay.
MONITOR_BASE = 0xf800
MONITOR_SIZE = 0x800

# The Orion reaches its hardware through memory, not through i8080 ports.
# The 8255 chips (keyboard, ROM-disk, user ports) occupy F400-F7FF, and the
# system latches (colour, RAM page, screen page) share F800-FFFF with the
# Monitor ROM: reads there return the ROM, writes set the latches.
IO_BASE = 0xf400
IO_SIZE = 0x400


class Orion128Machine(z80.I8080Machine):
    '''The Orion-128 machine: the i8080 core with the Orion's memory.

    The processor reads memory straight from the core, which is fast. Only
    writes need watching, so a single write handler forms the whole bus: it
    protects the Monitor ROM, captures the system latches, and leaves the
    8255 region idle. Banking, the keyboard and the disk controller are
    still to come.
    '''

    def __init__(self, monitor: bytes | None = None) -> None:
        super().__init__()
        self.__system_ports: dict[int, int] = {}
        if monitor is not None:
            self.load_monitor(monitor)

    def load_monitor(self, monitor: bytes) -> None:
        '''Load the 2K Monitor ROM, set up the bus and start at the entry.'''
        assert len(monitor) == MONITOR_SIZE
        self.set_memory_block(MONITOR_BASE, monitor)

        # Idle I/O reads as no key pressed and no ROM-disk present.
        self.set_memory_block(IO_BASE, b'\xff' * IO_SIZE)

        self.pc = MONITOR_BASE
        self.set_write_callback(self.__on_write)

    def __on_write(self, addr: int, value: int) -> None:
        # The Monitor ROM and the system latches sit at MONITOR_BASE and
        # above. Capture the latch writes and never touch the ROM.
        if addr >= MONITOR_BASE:
            self.__system_ports[addr] = value
            return

        # Leave the 8255 region idle, so the keyboard keeps reading no key
        # and the ROM-disk keeps reading absent.
        if addr >= IO_BASE:
            return

        # Ordinary RAM, including the screen.
        self.set_memory_block(addr, bytes([value]))

    def read_screen(self) -> npt.NDArray[np.uint8]:
        '''Return the screen as a SCREEN_HEIGHT by SCREEN_WIDTH array of
        pixels, each 0 or 1.'''
        video = np.frombuffer(
            self.memory, dtype=np.uint8, count=VIDEO_SIZE, offset=VIDEO_BASE)

        # Bytes go down a column, so the buffer is columns of pixels; put
        # the rows first, then expand each byte into its eight pixels.
        columns = video.reshape(SCREEN_WIDTH // 8, SCREEN_HEIGHT)
        return np.unpackbits(columns.T, axis=1)
