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

# The processor runs at about 2.5 MHz.
CPU_FREQUENCY = 2_500_000

# The Orion reaches its hardware through memory, not through i8080 ports.
# The 8255 chips (keyboard, ROM-disk, user ports) occupy F400-F7FF, and the
# system latches (colour, RAM page, screen page) share F800-FFFF with the
# Monitor ROM: reads there return the ROM, writes set the latches.
IO_BASE = 0xf400
IO_SIZE = 0x400

# The ROM-disk 8255 lives at F500: F500 reads data, F501 sets the address
# low byte, F502 the high byte. Writing the address makes the addressed
# byte appear at the data port for the Monitor to read.
ROMDISK_PORT = 0xf500

# The keyboard 8255 at F400: port A (F400) drives the scan columns active
# low, and the sense rows are read active low from port B (F401) for rows
# 0-7 and the top half of port C (F402) for rows 8-11. A pressed key is a
# (column, row) crossing that pulls its row low when its column is scanned.
KEYBOARD_SCAN = 0xf400
KEYBOARD_SENSE = 0xf401
KEYBOARD_SENSE_C = 0xf402

# Memory paging. The processor's page for the 0x0000-0xEFFF region is
# selected through port F9 (or the F900 latch). The selected page is
# exposed in the core's memory, so reads and writes run at full speed; the
# other pages are held aside as images. Switching pages saves the exposed
# page back to its image and copies the newly selected image into the
# address space. F000-FFFF is common to all pages and never swapped.
PAGE_SELECT_PORT = 0xf9
PAGE_SELECT = 0xf900
PAGED_SIZE = 0xf000

# Pages 1, 2 and 3 are ORDOS's read/write RAM-disks, drives B:, C: and D:.
# A preloaded RAM-disk goes to page 1, drive B:.
RAM_DISK_PAGE = 1

# Colour control at F800 (or port F8). Bit D2 turns colour on; without it
# the screen is monochrome. In 16-colour mode a colour byte at the same
# address in page 1 holds the background colour in its top nibble and the
# foreground in its bottom nibble, and the pixel bit chooses between them.
COLOUR_CONTROL = 0xf800
COLOUR_CONTROL_PORT = 0xf8
COLOUR_ON = 0x04

# Monochrome is the Orion's green on black.
_GREEN = (0x30, 0xff, 0x30)


# The 16 colours, one bit each for intensity, red, green and blue.
def _build_palette() -> npt.NDArray[np.uint8]:
    palette = np.zeros((16, 3), dtype=np.uint8)
    for code in range(16):
        level = 0xff if code & 0x08 else 0xaa
        palette[code] = (level if code & 0x04 else 0,
                         level if code & 0x02 else 0,
                         level if code & 0x01 else 0)
    return palette


_PALETTE = _build_palette()


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
        self.__romdisk = b''
        self.__romdisk_addr = 0
        self.__scan = 0xff
        self.__keys: set[tuple[int, int]] = set()
        self.__page_images = {page: bytearray(PAGED_SIZE) for page in range(4)}
        self.__current_page = 0
        self.__colour_control = 0
        if monitor is not None:
            self.load_monitor(monitor)

    def load_monitor(self, monitor: bytes) -> None:
        '''Load the 2K Monitor ROM, set up the bus and start at the entry.'''
        assert len(monitor) == MONITOR_SIZE
        self.set_memory_block(MONITOR_BASE, monitor)

        # Idle I/O reads as no key pressed and no ROM-disk present.
        self.set_memory_block(IO_BASE, b'\xff' * IO_SIZE)

        self.pc = MONITOR_BASE

        # Watch only the I/O and ROM region for writes. Every other write
        # goes straight to memory in the core, which keeps the processor
        # fast even while a program repaints the screen.
        self.set_write_callback(self.__on_write)
        self.mark_addrs(IO_BASE, 0x10000 - IO_BASE, self.WRITE_MARK)

        # Port F9 selects the memory page.
        self.set_output_callback(self.__on_output)

    def reset(self) -> None:
        '''Reset the processor to the Monitor, as the RESET key does.

        RAM, including the RAM-disks, is kept, so the Monitor re-boots ORDOS
        with everything still in place. The Monitor expects page 0 and a
        cleared colour mode.
        '''
        self.__select_page(0)
        self.__colour_control = 0
        self.pc = MONITOR_BASE

    def load_romdisk(self, romdisk: bytes) -> None:
        '''Attach a ROM-disk image, served through the F500 8255.'''
        self.__romdisk = romdisk
        self.__romdisk_addr = 0
        self.set_memory_block(ROMDISK_PORT, bytes([romdisk[0]]))

    def load_ram_disk(self, files: list[bytes]) -> None:
        '''Fill the RAM-disk (drive B:, page 1) with ORDOS file records.

        Each ORDOS file is a complete record: an 8-byte name, a 2-byte load
        address, a 2-byte size, four more header bytes, then the data. The
        records lie end to end and an FF byte closes the directory. ORDOS
        keeps such a preloaded disk instead of clearing it at start-up.

        On disk the size field is the data length, and ORDOS steps to the
        next record by it. A stored .ORD file instead holds the whole file
        length there, 16 too many, so rewrite it to the data length.
        '''
        image = bytearray(PAGED_SIZE)
        offset = 0
        for record in files:
            entry = bytearray(record)
            data_size = len(entry) - 16
            entry[10:12] = data_size.to_bytes(2, 'little')
            image[offset:offset + len(entry)] = entry
            offset += len(entry)
        image[offset] = 0xff
        self.__page_images[RAM_DISK_PAGE][:] = image

    def set_keys(self, keys: set[tuple[int, int]]) -> None:
        '''Set the pressed keys as (column, row) matrix crossings.'''
        self.__keys = set(keys)
        self.__update_keyboard()

    def __update_keyboard(self) -> None:
        # A pressed key pulls its sense row low while its scan column is
        # driven low. Rows 0-7 report on port B, rows 8-11 on the top of
        # port C.
        sense_b = 0xff
        sense_c = 0xff
        for column, row in self.__keys:
            if not (self.__scan >> column) & 1:
                if row < 8:
                    sense_b &= ~(1 << row) & 0xff
                else:
                    sense_c &= ~(1 << (row - 8 + 4)) & 0xff
        self.set_memory_block(KEYBOARD_SENSE, bytes([sense_b]))
        self.set_memory_block(KEYBOARD_SENSE_C, bytes([sense_c]))

    def __on_write(self, addr: int, value: int) -> None:
        # Only F400-FFFF is marked for this handler; the paged region below
        # writes straight to the core's memory.
        # The Monitor ROM and the system latches sit at MONITOR_BASE and
        # above. Capture the latch writes and never touch the ROM. The F900
        # latch also selects the memory page.
        if addr >= MONITOR_BASE:
            self.__system_ports[addr] = value
            if addr == PAGE_SELECT:
                self.__select_page(value)
            elif addr == COLOUR_CONTROL:
                self.__colour_control = value
            return

        # The 8255 region. Writing the ROM-disk address ports makes the
        # addressed byte appear at its data port. Writing the keyboard scan
        # column updates the sense rows for the pressed keys.
        if self.__romdisk and ROMDISK_PORT < addr <= ROMDISK_PORT + 2:
            self.__set_romdisk_address(addr, value)
        elif addr == KEYBOARD_SCAN:
            self.__scan = value
            self.__update_keyboard()

    def __on_output(self, port: int, value: int) -> None:
        if port & 0xff == PAGE_SELECT_PORT:
            self.__select_page(value)
        elif port & 0xff == COLOUR_CONTROL_PORT:
            self.__colour_control = value

    def __select_page(self, page: int) -> None:
        page &= 0x03
        if page == self.__current_page:
            return

        # Save the exposed page back to its image, then expose the newly
        # selected page. The core's memory always holds the current page,
        # so ordinary reads and writes stay at full speed.
        self.__page_images[self.__current_page][:] = self.memory[:PAGED_SIZE]
        self.set_memory_block(0, self.__page_images[page])
        self.__current_page = page

    def __set_romdisk_address(self, addr: int, value: int) -> None:
        if addr == ROMDISK_PORT + 1:
            self.__romdisk_addr = (self.__romdisk_addr & 0xff00) | value
        else:
            self.__romdisk_addr = (self.__romdisk_addr & 0x00ff) | (value << 8)
        byte = self.__romdisk[self.__romdisk_addr % len(self.__romdisk)]
        self.set_memory_block(ROMDISK_PORT, bytes([byte]))

    def __page_memory(self, page: int) -> bytes | bytearray | memoryview:
        if page == self.__current_page:
            return self.memory
        return self.__page_images[page]

    def read_screen(self) -> npt.NDArray[np.uint8]:
        '''Return the screen as a SCREEN_HEIGHT by SCREEN_WIDTH array of
        pixels, each 0 or 1.'''
        video = np.frombuffer(
            self.__page_memory(0), dtype=np.uint8, count=VIDEO_SIZE,
            offset=VIDEO_BASE)

        # Bytes go down a column, so the buffer is columns of pixels; put
        # the rows first, then expand each byte into its eight pixels.
        columns = video.reshape(SCREEN_WIDTH // 8, SCREEN_HEIGHT)
        return np.unpackbits(columns.T, axis=1)

    def render(self) -> npt.NDArray[np.uint8]:
        '''Return the screen as a SCREEN_HEIGHT by SCREEN_WIDTH RGB frame,
        in the current colour mode.'''
        pixels = self.read_screen()

        # Monochrome until a program turns colour on.
        if not self.__colour_control & COLOUR_ON:
            frame = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH, 3), dtype=np.uint8)
            frame[pixels != 0] = _GREEN
            return frame

        # 16-colour: the colour byte for each pixel byte is at the same
        # address in page 1. Its top nibble is the background colour and its
        # bottom nibble the foreground; the pixel bit chooses between them.
        colour = np.frombuffer(
            self.__page_memory(1), dtype=np.uint8, count=VIDEO_SIZE,
            offset=VIDEO_BASE)
        per_byte = colour.reshape(SCREEN_WIDTH // 8, SCREEN_HEIGHT).T
        per_pixel = np.repeat(per_byte, 8, axis=1)
        foreground = per_pixel & 0x0f
        background = per_pixel >> 4
        index = np.where(pixels != 0, foreground, background)
        return _PALETTE[index]
