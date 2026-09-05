#   Orion-128 home computer emulator.
#   https://github.com/kosarev/orion128
#
#   Copyright (C) 2026 Ivan Kosarev.
#   mail@ivankosarev.com
#
#   Published under the MIT license.

'''The keyboard layouts: host keys to Orion matrix crossings.

The Orion was built with one of two keyboards, and its Monitor must match.
A Keyboard maps the pressed host keys to (column, row) crossings of the
F400 8255 matrix. Every context reads the matrix -- the Monitor's own input
routines, and games that scan it directly -- so presenting the right
crossings is what makes a key type the intended character everywhere. The
crossings were read off each Monitor by driving them and seeing which
character its decoder returns.

The Orion's shift is not the PC's. On the MS7007 the decoder XORs bit 4 of
a symbol, so the ';' key shifted gives '+', not ':', and ':' is a key of
its own. So a shifted host key is mapped to the crossings that yield the
US-layout character on this keyboard, taken from the same calibration,
rather than to the Orion shift plus the base key.
'''

import sdl2

Crossing = tuple[int, int]

_HOST_SHIFT = frozenset({sdl2.SDLK_LSHIFT, sdl2.SDLK_RSHIFT})


class Keyboard:
    '''One Orion keyboard: the base crossings, the shift crossing, and the
    crossings that produce the shifted symbols.'''

    def __init__(self, keys: dict[int, Crossing], shift: Crossing,
                 shifted: dict[int, frozenset[Crossing]]) -> None:
        self.__keys = keys
        self.__shift = shift
        self.__shifted = shifted

    def crossings(self, held: set[int]) -> set[Crossing]:
        '''The Orion (column, row) crossings for the held host keys.'''
        shift = bool(held & _HOST_SHIFT)
        result: set[Crossing] = set()
        for key in held:
            if key in _HOST_SHIFT:
                continue
            if shift and key in self.__shifted:
                result |= self.__shifted[key]
            elif key in self.__keys:
                result.add(self.__keys[key])
                if shift:
                    result.add(self.__shift)
        return result


# MS7007 base map: letters (uppercase), digits, the unshifted punctuation,
# and the control keys.
_MS7007_KEYS: dict[int, Crossing] = {
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
}

# MS7007 shifted symbols: host key to the crossings for its US-layout
# shifted character. Every symbol has a key on this keyboard; a few need
# the Orion shift as well (its own key is the shifted form).
_MS7007_SHIFTED: dict[int, frozenset[Crossing]] = {
    sdl2.SDLK_1: frozenset({(2, 2)}),           # !
    sdl2.SDLK_2: frozenset({(4, 1)}),           # @
    sdl2.SDLK_3: frozenset({(2, 4)}),           # #
    sdl2.SDLK_4: frozenset({(1, 7)}),           # $
    sdl2.SDLK_5: frozenset({(2, 5)}),           # %
    sdl2.SDLK_6: frozenset({(5, 2)}),           # ^
    sdl2.SDLK_7: frozenset({(2, 6)}),           # &
    sdl2.SDLK_8: frozenset({(5, 9), (0, 7)}),   # *
    sdl2.SDLK_9: frozenset({(1, 1)}),           # (
    sdl2.SDLK_0: frozenset({(0, 1)}),           # )
    sdl2.SDLK_MINUS: frozenset({(7, 6)}),       # _
    sdl2.SDLK_EQUALS: frozenset({(6, 3)}),      # +
    sdl2.SDLK_SEMICOLON: frozenset({(0, 7)}),   # :
    sdl2.SDLK_QUOTE: frozenset({(2, 3)}),       # "
    sdl2.SDLK_COMMA: frozenset({(5, 1)}),       # <
    sdl2.SDLK_PERIOD: frozenset({(6, 6)}),      # >
    sdl2.SDLK_SLASH: frozenset({(5, 9), (0, 5)}),        # ?
    sdl2.SDLK_LEFTBRACKET: frozenset({(5, 9), (2, 0)}),  # {
    sdl2.SDLK_RIGHTBRACKET: frozenset({(5, 9), (2, 1)}),  # }
    sdl2.SDLK_BACKSLASH: frozenset({(5, 9), (6, 0)}),    # |
    sdl2.SDLK_BACKQUOTE: frozenset({(5, 9), (5, 2)}),    # ~
}

MS7007 = Keyboard(_MS7007_KEYS, (5, 9), _MS7007_SHIFTED)

# RK-86 base map. A smaller keyboard: the regular RK-86 ASCII grid, letters
# and digits in columns 2-7, the control keys in columns 0-1. Games that
# scan the matrix directly, such as MANIC, rely on these exact positions.
_RK86_KEYS: dict[int, Crossing] = {
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

# RK-86 shifted symbols. Only these exist on the keyboard; the rest of the
# PC's shifted symbols (!#$%&*()+=<>?) have no key here.
_RK86_SHIFTED: dict[int, frozenset[Crossing]] = {
    sdl2.SDLK_2: frozenset({(4, 0)}),           # @
    sdl2.SDLK_6: frozenset({(7, 6)}),           # ^
    sdl2.SDLK_SEMICOLON: frozenset({(3, 2)}),   # :
}

RK86 = Keyboard(_RK86_KEYS, (4, 9), _RK86_SHIFTED)
