#   Orion-128 home computer emulator.
#   https://github.com/kosarev/orion128
#
#   Copyright (C) 2026 Ivan Kosarev.
#   mail@ivankosarev.com
#
#   Published under the MIT license.

import orion128


def test_load_monitor() -> None:
    # A synthetic ROM whose first byte is the reset jump, as the real
    # Monitor's is.
    monitor = bytes([0xc3, 0x42, 0xf8]) + bytes(orion128.MONITOR_SIZE - 3)
    machine = orion128.Orion128Machine(monitor)
    assert machine.pc == orion128.MONITOR_BASE
    start = orion128.MONITOR_BASE
    assert bytes(machine.memory[start:start + 3]) == bytes([0xc3, 0x42, 0xf8])


def test_io_bus() -> None:
    # A monitor that stores to a system latch (F900) and to RAM (0x1234),
    # then halts.
    code = bytes([
        0x3e, 0x99,        # MVI A, 0x99
        0x32, 0x00, 0xf9,  # STA 0xF900   -- a latch; the ROM must survive
        0x32, 0x34, 0x12,  # STA 0x1234   -- ordinary RAM
        0x76,              # HLT
    ])
    monitor = code + bytes(orion128.MONITOR_SIZE - len(code))
    machine = orion128.Orion128Machine(monitor)
    machine.ticks_to_stop = 1000
    machine.run()

    # The write to F900 was captured as a latch, not stored, so the ROM
    # byte there is unchanged.
    assert machine.memory[0xf900] == monitor[0xf900 - orion128.MONITOR_BASE]
    # The write to RAM went through.
    assert machine.memory[0x1234] == 0x99


def test_romdisk() -> None:
    # A monitor that sets the ROM-disk address to 0x1234, reads the data
    # port, stores the byte to RAM, then halts.
    code = bytes([
        0x3e, 0x34,        # MVI A, 0x34
        0x32, 0x01, 0xf5,  # STA 0xF501   -- address low
        0x3e, 0x12,        # MVI A, 0x12
        0x32, 0x02, 0xf5,  # STA 0xF502   -- address high
        0x3a, 0x00, 0xf5,  # LDA 0xF500   -- the data port
        0x32, 0x00, 0x10,  # STA 0x1000
        0x76,              # HLT
    ])
    monitor = code + bytes(orion128.MONITOR_SIZE - len(code))
    machine = orion128.Orion128Machine(monitor)

    romdisk = bytearray(0x10000)
    romdisk[0x1234] = 0x5a
    machine.load_romdisk(bytes(romdisk))

    machine.ticks_to_stop = 1000
    machine.run()
    assert machine.memory[0x1000] == 0x5a


def test_keyboard() -> None:
    # A monitor that drives scan column 2 low, reads the sense rows, stores
    # them to RAM, then halts.
    code = bytes([
        0x3e, 0xfb,        # MVI A, 0xFB   -- column 2 low
        0x32, 0x00, 0xf4,  # STA 0xF400    -- scan
        0x3a, 0x01, 0xf4,  # LDA 0xF401    -- sense
        0x32, 0x00, 0x10,  # STA 0x1000
        0x76,              # HLT
    ])
    monitor = code + bytes(orion128.MONITOR_SIZE - len(code))
    machine = orion128.Orion128Machine(monitor)

    # A key at column 2, row 3, plus one on another column that must stay
    # invisible while column 2 is scanned.
    machine.set_keys({(2, 3), (5, 6)})
    machine.ticks_to_stop = 1000
    machine.run()

    # Row 3 pulled low, the rest high: 0xFF & ~(1 << 3) == 0xF7.
    assert machine.memory[0x1000] == 0xf7


def test_screen_pixel_layout() -> None:
    machine = orion128.Orion128Machine()
    screen = machine.read_screen()
    assert screen.shape == (orion128.SCREEN_HEIGHT, orion128.SCREEN_WIDTH)
    assert not screen.any()

    # The first video byte is the leftmost eight pixels of the top row,
    # the most significant bit first.
    machine.set_memory_block(orion128.VIDEO_BASE, bytes([0x80]))
    screen = machine.read_screen()
    assert screen[0, 0] == 1
    assert screen[0, 1] == 0

    # The least significant bit of that byte is its rightmost pixel.
    machine.set_memory_block(orion128.VIDEO_BASE, bytes([0x01]))
    screen = machine.read_screen()
    assert screen[0, 7] == 1
    assert screen[0, 6] == 0

    # Stepping the address by the screen height moves right by one byte.
    machine.set_memory_block(orion128.VIDEO_BASE, bytes([0x00]))
    machine.set_memory_block(
        orion128.VIDEO_BASE + orion128.SCREEN_HEIGHT, bytes([0x80]))
    screen = machine.read_screen()
    assert screen[0, 8] == 1

    # Stepping the address by one moves down by one row.
    machine.set_memory_block(
        orion128.VIDEO_BASE + orion128.SCREEN_HEIGHT, bytes([0x00]))
    machine.set_memory_block(orion128.VIDEO_BASE + 1, bytes([0x80]))
    screen = machine.read_screen()
    assert screen[1, 0] == 1
