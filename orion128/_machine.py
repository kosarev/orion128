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


class Orion128Machine(z80.I8080Machine):
    '''The Orion-128 machine: the i8080 core with the Orion's memory.

    Only the memory and the screen layout are modelled so far. Memory
    banking, ports, the keyboard and the disk controller come later.
    '''

    def read_screen(self) -> npt.NDArray[np.uint8]:
        '''Return the screen as a SCREEN_HEIGHT by SCREEN_WIDTH array of
        pixels, each 0 or 1.'''
        video = np.frombuffer(
            self.memory, dtype=np.uint8, count=VIDEO_SIZE, offset=VIDEO_BASE)

        # Bytes go down a column, so the buffer is columns of pixels; put
        # the rows first, then expand each byte into its eight pixels.
        columns = video.reshape(SCREEN_WIDTH // 8, SCREEN_HEIGHT)
        return np.unpackbits(columns.T, axis=1)
