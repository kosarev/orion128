# orion128

An emulator of the Orion-128, a Soviet home computer built around the
KR580VM80A processor (an i8080 clone).

orion128 emulates the hardware — memory-mapped video, the keyboard, ports and
the disk controller — and runs the real ROM and software on top of it. It is
built on the [z80](https://github.com/kosarev/z80) package for the i8080 core
and aims to stay in pure Python. The display is built on PySDL2 and numpy.

It ships with a Monitor and an ORDOS ROM-disk, so it boots a working system
out of the box:

```shell
orion128
```

`--monitor PATH` and `--romdisk PATH` replace the bundled ROMs, and
`--ord PATH` preloads an ORDOS file (`.ORD` or `.BRU`) onto the RAM-disk
(drive B:).

The bundled ROMs are the copyright of their original authors and are not
covered by this package's MIT licence; see `orion128/ROMS.txt`.

This is early work in progress.
