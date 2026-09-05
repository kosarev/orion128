# Changelog


## 0.1.0b1

- Floppy disk controller (the KR1818VG93): reads and writes disk images, up to four drives at once. The ORDOS file manager copies files to and from disks, and CP/M boots and runs from a system disk. Disk changes are kept in memory, so the image files are left as they are.
- The RK-86 keyboard machine (`--rk86`), with its own bundled Monitor and keyboard layout, for software written for that keyboard.
- The alternative screens (the FA00 switch), so a program can draw one screen while another is shown.
- PC keys are mapped to the Orion keys by the character they produce, so `:`, `;` and `#` type as themselves; games that scan the keyboard directly still work.
- Disk images and ORDOS files are given as plain command-line arguments.


## 0.1.0a1

First alpha of the Orion-128 emulator.

- Emulates the hardware -- memory-mapped video (monochrome and 16-colour), the MS7007 keyboard, the ports and the ROM-disk -- and runs the real ROM and software on top of it. Built on the z80 package for the i8080 core.
- Boots a working system out of the box: it bundles the MS7007 Monitor and an ORDOS 4.03 ROM-disk. `--monitor` and `--romdisk` replace them.
- Preloads ORDOS files (`.ORD` or `.BRU`) onto the RAM-disk, given as arguments.
- SDL display; F12 is the RESET button and F10 closes the emulator.
