#   Orion-128 home computer emulator.
#   https://github.com/kosarev/orion128
#
#   Copyright (C) 2026 Ivan Kosarev.
#   mail@ivankosarev.com
#
#   Published under the MIT license.

'''The keyboard layouts: host key to Orion matrix crossing.

The Orion was built with one of two keyboards, and its Monitor must match.
Each layout maps a host SDL key to a (column, row) crossing of the F400
8255 matrix: the column is a port A scan line, the row a port B sense line
(0-7) or the top of port C (8-11). The crossings were read off the Monitor
itself, by driving each one and seeing which character it decodes, so host
letters and digits reach the Orion keys of the same name.
'''

import sdl2

# The MS7007 keyboard, the author's machine.
MS7007_KEYS = {
    sdl2.SDLK_a: (4, 4), sdl2.SDLK_b: (4, 0), sdl2.SDLK_c: (3, 2),
    sdl2.SDLK_d: (3, 1), sdl2.SDLK_e: (2, 7), sdl2.SDLK_f: (3, 11),
    sdl2.SDLK_g: (3, 6), sdl2.SDLK_h: (7, 0), sdl2.SDLK_i: (4, 7),
    sdl2.SDLK_j: (2, 11), sdl2.SDLK_k: (3, 4), sdl2.SDLK_l: (3, 0),
    sdl2.SDLK_m: (5, 4), sdl2.SDLK_n: (3, 5), sdl2.SDLK_o: (4, 6),
    sdl2.SDLK_p: (3, 7), sdl2.SDLK_q: (4, 11), sdl2.SDLK_r: (4, 5),
    sdl2.SDLK_s: (5, 3), sdl2.SDLK_t: (5, 5), sdl2.SDLK_u: (3, 3),
    sdl2.SDLK_v: (6, 1), sdl2.SDLK_w: (4, 3), sdl2.SDLK_x: (5, 6),
    sdl2.SDLK_y: (4, 2), sdl2.SDLK_z: (7, 1),
    sdl2.SDLK_0: (6, 10), sdl2.SDLK_1: (6, 11), sdl2.SDLK_2: (7, 11),
    sdl2.SDLK_3: (0, 11), sdl2.SDLK_4: (6, 2), sdl2.SDLK_5: (7, 2),
    sdl2.SDLK_6: (0, 2), sdl2.SDLK_7: (6, 9), sdl2.SDLK_8: (7, 9),
    sdl2.SDLK_9: (0, 9),
    sdl2.SDLK_PERIOD: (7, 10), sdl2.SDLK_COMMA: (1, 9),
    sdl2.SDLK_SEMICOLON: (1, 11), sdl2.SDLK_SLASH: (0, 5),
    sdl2.SDLK_MINUS: (2, 9), sdl2.SDLK_EQUALS: (0, 6),
    sdl2.SDLK_QUOTE: (1, 0), sdl2.SDLK_LEFTBRACKET: (2, 0),
    sdl2.SDLK_RIGHTBRACKET: (2, 1), sdl2.SDLK_BACKSLASH: (6, 0),
    sdl2.SDLK_SPACE: (0, 0), sdl2.SDLK_RETURN: (0, 10),
    sdl2.SDLK_LEFT: (5, 0), sdl2.SDLK_RIGHT: (6, 7),
    sdl2.SDLK_UP: (7, 5), sdl2.SDLK_DOWN: (6, 5),
    sdl2.SDLK_BACKSPACE: (6, 4), sdl2.SDLK_ESCAPE: (1, 10),
    # Shift gives the Orion's shifted characters (and lowercase letters).
    sdl2.SDLK_LSHIFT: (5, 9), sdl2.SDLK_RSHIFT: (5, 9),
}

# The RK-86 keyboard (the --rk86 Monitor), read off the M2rk Monitor. Its
# matrix is the regular RK-86 ASCII grid: letters and digits in columns
# 2-7, the control keys in columns 0-1. Games that scan the matrix directly,
# such as MANIC, rely on these exact positions, so their keys land nowhere
# on the MS7007 layout.
RK86_KEYS = {
    sdl2.SDLK_a: (4, 1), sdl2.SDLK_b: (4, 2), sdl2.SDLK_c: (4, 3),
    sdl2.SDLK_d: (4, 4), sdl2.SDLK_e: (4, 5), sdl2.SDLK_f: (4, 6),
    sdl2.SDLK_g: (4, 7), sdl2.SDLK_h: (5, 0), sdl2.SDLK_i: (5, 1),
    sdl2.SDLK_j: (5, 2), sdl2.SDLK_k: (5, 3), sdl2.SDLK_l: (5, 4),
    sdl2.SDLK_m: (5, 5), sdl2.SDLK_n: (5, 6), sdl2.SDLK_o: (5, 7),
    sdl2.SDLK_p: (6, 0), sdl2.SDLK_q: (6, 1), sdl2.SDLK_r: (6, 2),
    sdl2.SDLK_s: (6, 3), sdl2.SDLK_t: (6, 4), sdl2.SDLK_u: (6, 5),
    sdl2.SDLK_v: (6, 6), sdl2.SDLK_w: (6, 7), sdl2.SDLK_x: (7, 0),
    sdl2.SDLK_y: (7, 1), sdl2.SDLK_z: (7, 2),
    sdl2.SDLK_0: (2, 0), sdl2.SDLK_1: (2, 1), sdl2.SDLK_2: (2, 2),
    sdl2.SDLK_3: (2, 3), sdl2.SDLK_4: (2, 4), sdl2.SDLK_5: (2, 5),
    sdl2.SDLK_6: (2, 6), sdl2.SDLK_7: (2, 7), sdl2.SDLK_8: (3, 0),
    sdl2.SDLK_9: (3, 1),
    sdl2.SDLK_SEMICOLON: (3, 3), sdl2.SDLK_COMMA: (3, 4),
    sdl2.SDLK_MINUS: (3, 5), sdl2.SDLK_PERIOD: (3, 6),
    sdl2.SDLK_SLASH: (3, 7), sdl2.SDLK_LEFTBRACKET: (7, 3),
    sdl2.SDLK_RIGHTBRACKET: (7, 5), sdl2.SDLK_BACKSLASH: (7, 4),
    sdl2.SDLK_SPACE: (7, 7), sdl2.SDLK_RETURN: (1, 2),
    sdl2.SDLK_BACKSPACE: (1, 4), sdl2.SDLK_TAB: (1, 0),
    sdl2.SDLK_ESCAPE: (0, 2),
    # The RK-86 cursor codes: left 08, right 18, up 19, down 1A.
    sdl2.SDLK_LEFT: (1, 4), sdl2.SDLK_RIGHT: (1, 6),
    sdl2.SDLK_UP: (1, 5), sdl2.SDLK_DOWN: (1, 7),
}
