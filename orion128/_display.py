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

from ._keyboard import MS7007_KEYS
from ._machine import SCREEN_HEIGHT, SCREEN_WIDTH

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
