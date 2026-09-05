#   Orion-128 home computer emulator.
#   https://github.com/kosarev/orion128
#
#   Copyright (C) 2026 Ivan Kosarev.
#   mail@ivankosarev.com
#
#   Published under the MIT license.

import ctypes
import os

import numpy as np
import numpy.typing as npt
import sdl2

from ._machine import SCREEN_HEIGHT, SCREEN_WIDTH

# The MS7007 keyboard: host key to (column, row) matrix crossing. The
# columns are the port A scan lines, the rows the port B sense lines (0-7)
# and the top of port C (8-11). The crossings were read off the Monitor
# itself, by pressing each one and seeing which character it decodes, so
# the host letter and digit keys reach the Orion keys of the same name.
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

# The RK-86 keyboard, for machines built with it (the --rk86 Monitor). Read
# off the M2rk Monitor the same way. Its matrix is the regular RK-86 ASCII
# grid: letters and digits in columns 2-7, the control keys in columns 0-1.
# Games that scan the matrix directly, such as MANIC, rely on these exact
# positions, so their keys land nowhere on the MS7007 layout.
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

# The RESET key is a hardware button, not a matrix key, so it has its own
# host key.
_RESET_KEY = sdl2.SDLK_F12

# F10 closes the emulator, as an alternative to closing the window.
_QUIT_KEY = sdl2.SDLK_F10


class Display:
    '''A window showing the Orion screen, built on SDL.

    It takes the pixel bitmap from the machine and shows it in black and
    white, scaled up so the small screen is comfortable to look at.
    '''

    def __init__(self, scale: int = 2, title: str = 'Orion-128',
                 keys: dict[int, tuple[int, int]] = MS7007_KEYS) -> None:
        # On Wayland, use the Wayland driver so the window follows the
        # system display scaling instead of being upscaled by XWayland.
        on_wayland = 'WAYLAND_DISPLAY' in os.environ
        if on_wayland and 'SDL_VIDEODRIVER' not in os.environ:
            os.environ['SDL_VIDEODRIVER'] = 'wayland'

        sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)

        # SDL_WINDOW_ALLOW_HIGHDPI makes the drawable the full device-pixel
        # size on a scaled display, so the window is the intended physical
        # size and the screen is drawn crisply rather than being upscaled.
        self.__window = sdl2.SDL_CreateWindow(
            title.encode(),
            sdl2.SDL_WINDOWPOS_CENTERED, sdl2.SDL_WINDOWPOS_CENTERED,
            SCREEN_WIDTH * scale, SCREEN_HEIGHT * scale,
            sdl2.SDL_WINDOW_SHOWN | sdl2.SDL_WINDOW_ALLOW_HIGHDPI)

        self.__renderer = sdl2.SDL_CreateRenderer(self.__window, -1, 0)

        # A streaming texture the size of the screen; SDL scales it up to
        # fill the window when it is copied.
        self.__texture = sdl2.SDL_CreateTexture(
            self.__renderer, sdl2.SDL_PIXELFORMAT_RGB24,
            sdl2.SDL_TEXTUREACCESS_STREAMING, SCREEN_WIDTH, SCREEN_HEIGHT)

        self.__matrix = keys
        self.__quit = False
        self.__reset_pressed = False
        self.__keys_down: set[int] = set()

    def update(self, frame: npt.NDArray[np.uint8]) -> None:
        '''Show the given SCREEN_HEIGHT by SCREEN_WIDTH RGB frame.'''
        frame = np.ascontiguousarray(frame, dtype=np.uint8)
        sdl2.SDL_UpdateTexture(
            self.__texture, None, frame.ctypes.data, SCREEN_WIDTH * 3)
        sdl2.SDL_RenderClear(self.__renderer)
        sdl2.SDL_RenderCopy(self.__renderer, self.__texture, None, None)
        sdl2.SDL_RenderPresent(self.__renderer)

    def closed(self) -> bool:
        '''Process window events, then report whether close was requested.'''
        event = sdl2.SDL_Event()
        while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == sdl2.SDL_QUIT:
                self.__quit = True
            elif event.type == sdl2.SDL_KEYDOWN:
                key = int(event.key.keysym.sym)
                if key == _QUIT_KEY:
                    self.__quit = True
                elif key == _RESET_KEY:
                    self.__reset_pressed = True
                else:
                    self.__keys_down.add(key)
            elif event.type == sdl2.SDL_KEYUP:
                self.__keys_down.discard(int(event.key.keysym.sym))
        return self.__quit

    def pressed_keys(self) -> set[tuple[int, int]]:
        '''The pressed keys as Orion (column, row) matrix crossings.'''
        return {self.__matrix[key]
                for key in self.__keys_down if key in self.__matrix}

    def take_reset(self) -> bool:
        '''Report whether the RESET key was pressed, and clear it.'''
        pressed = self.__reset_pressed
        self.__reset_pressed = False
        return pressed

    def close(self) -> None:
        sdl2.SDL_DestroyTexture(self.__texture)
        sdl2.SDL_DestroyRenderer(self.__renderer)
        sdl2.SDL_DestroyWindow(self.__window)
        sdl2.SDL_Quit()
