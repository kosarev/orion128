# orion128

An emulator of the Orion-128, a Soviet home computer built around the
KR580VM80A processor (an i8080 clone).

Unlike a CP/M emulator that fakes the BIOS at its call vectors, orion128
emulates the actual hardware — memory-mapped video, the keyboard, ports and
the disk controller — and runs the real ROM and software on top of it. It is
built on the [z80](https://github.com/kosarev/z80) package for the i8080 core
and aims to stay in pure Python. The display is built on PySDL2 and numpy.

This is early work in progress.
