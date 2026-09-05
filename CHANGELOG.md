# Changelog


## 0.1.0a1

First alpha of the Orion-128 emulator.

- Emulates the hardware -- memory-mapped video (monochrome and 16-colour), the MS7007 keyboard, the ports and the ROM-disk -- and runs the real ROM and software on top of it. Built on the z80 package for the i8080 core.
- Boots a working system out of the box: it bundles the MS7007 Monitor and an ORDOS 4.03 ROM-disk. `--monitor` and `--romdisk` replace them.
- Preloads ORDOS files (`.ORD` or `.BRU`) onto the RAM-disk, given as arguments.
- SDL display; F12 is the RESET button and F10 closes the emulator.
