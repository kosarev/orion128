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
# columns are the port A scan lines, the rows the port B sense lines. The
# crossings are taken from the MS7007 matrix, laid over a host keyboard by
# position, so the host letter and digit keys reach the same Orion keys.
_KEY_MATRIX = {
    sdl2.SDLK_a: (0, 1), sdl2.SDLK_b: (4, 7), sdl2.SDLK_c: (3, 0),
    sdl2.SDLK_d: (2, 1), sdl2.SDLK_e: (2, 2), sdl2.SDLK_f: (3, 1),
    sdl2.SDLK_g: (4, 1), sdl2.SDLK_h: (4, 6), sdl2.SDLK_i: (2, 5),
    sdl2.SDLK_j: (3, 6), sdl2.SDLK_k: (2, 6), sdl2.SDLK_l: (1, 6),
    sdl2.SDLK_m: (2, 7), sdl2.SDLK_n: (3, 7), sdl2.SDLK_o: (1, 5),
    sdl2.SDLK_p: (0, 5), sdl2.SDLK_q: (0, 2), sdl2.SDLK_r: (3, 2),
    sdl2.SDLK_s: (1, 1), sdl2.SDLK_t: (4, 2), sdl2.SDLK_u: (3, 5),
    sdl2.SDLK_v: (4, 0), sdl2.SDLK_w: (1, 2), sdl2.SDLK_x: (2, 0),
    sdl2.SDLK_y: (4, 5), sdl2.SDLK_z: (1, 0),
    sdl2.SDLK_0: (0, 4), sdl2.SDLK_1: (0, 3), sdl2.SDLK_2: (1, 3),
    sdl2.SDLK_3: (2, 3), sdl2.SDLK_4: (3, 3), sdl2.SDLK_5: (4, 3),
    sdl2.SDLK_6: (4, 4), sdl2.SDLK_7: (3, 4), sdl2.SDLK_8: (2, 4),
    sdl2.SDLK_9: (1, 4),
    sdl2.SDLK_SPACE: (0, 7), sdl2.SDLK_RETURN: (0, 6),
    sdl2.SDLK_LSHIFT: (0, 0), sdl2.SDLK_RSHIFT: (1, 7),
}


class Display:
    '''A window showing the Orion screen, built on SDL.

    It takes the pixel bitmap from the machine and shows it in black and
    white, scaled up so the small screen is comfortable to look at.
    '''

    def __init__(self, scale: int = 2, title: str = 'Orion-128') -> None:
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

        self.__quit = False
        self.__keys_down: set[int] = set()

    def update(self, screen: npt.NDArray[np.uint8]) -> None:
        '''Show the given SCREEN_HEIGHT by SCREEN_WIDTH pixel bitmap.'''
        # Turn each 0 or 1 pixel into a black or white RGB triple.
        frame = np.empty((SCREEN_HEIGHT, SCREEN_WIDTH, 3), dtype=np.uint8)
        frame[:] = (screen * 0xff)[:, :, np.newaxis]

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
                self.__keys_down.add(int(event.key.keysym.sym))
            elif event.type == sdl2.SDL_KEYUP:
                self.__keys_down.discard(int(event.key.keysym.sym))
        return self.__quit

    def pressed_keys(self) -> set[tuple[int, int]]:
        '''The pressed keys as Orion (column, row) matrix crossings.'''
        return {_KEY_MATRIX[key]
                for key in self.__keys_down if key in _KEY_MATRIX}

    def close(self) -> None:
        sdl2.SDL_DestroyTexture(self.__texture)
        sdl2.SDL_DestroyRenderer(self.__renderer)
        sdl2.SDL_DestroyWindow(self.__window)
        sdl2.SDL_Quit()
