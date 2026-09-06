# Changelog


## 0.1.0

Disk images from the host, built on cpm80's file system:

- Commands named after their CP/M counterparts: `dir` lists every user area at once, a line per file with the user number, name and size; `save` copies files onto a disk or off it, source then destination; `ren`, `era`, `format` and `sysgen` rename, delete, make a blank disk and copy the system tracks between disks or to and from a plain file.
- `split` takes an image apart into a directory, every byte into a part: the system tracks, the directory, the live files, the erased files with the blocks taken over since filled in, the unallocated blocks holding data, each with a note of what the report says about it. The raw material for recovering erased files by hand.
- `strip` writes ORDOS files in their canonical form, so two copies of one program are byte-identical.
- `--help`.

Also:

- A preloaded ORDOS file is checked against its header and a broken one reported, rather than guessed at and quietly trimmed.
- PySDL2 is imported only when the window opens, so the disk commands run without its start-up warning.


## 0.1.0b3

- Show the README screenshot on PyPI by referencing it with an absolute URL.


## 0.1.0b2

- Floppy disk controller (the KR1818VG93): reads and writes disk images, up to four drives at once. The ORDOS file manager copies files to and from disks, and CP/M boots and runs from a system disk. The bundled ROM-disk now carries the LDOS loader, so CP/M boots with no extra ROMs. Disk changes are kept in memory, so the image files are left as they are.
- The RK-86 keyboard machine (`--rk86`), with its own bundled Monitor and keyboard layout, for software written for that keyboard.
- A Z80 core (`--z80`), for software that uses Z80 instructions. The Orion hardware is now a mixin combined with either the i8080 or the Z80 core.
- The alternative screens (the FA00 switch), so a program can draw one screen while another is shown.
- The 4-colour graphics mode: each pixel takes one bit from page 0 and one from page 1 at the same address, giving it its own colour from one of two palettes.
- PC keys are mapped to the Orion keys by the character they produce, so `:`, `;` and `#` type as themselves; games that scan the keyboard directly still work.
- Disk images and ORDOS files are given as plain command-line arguments.


## 0.1.0a1

First alpha of the Orion-128 emulator.

- Emulates the hardware -- memory-mapped video (monochrome and 16-colour), the MS7007 keyboard, the ports and the ROM-disk -- and runs the real ROM and software on top of it. Built on the z80 package for the i8080 core.
- Boots a working system out of the box: it bundles the MS7007 Monitor and an ORDOS 4.03 ROM-disk. `--monitor` and `--romdisk` replace them.
- Preloads ORDOS files (`.ORD` or `.BRU`) onto the RAM-disk, given as arguments.
- SDL display; F12 is the RESET button and F10 closes the emulator.
