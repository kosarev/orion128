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
