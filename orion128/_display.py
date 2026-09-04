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
        '''Report whether the user has asked to close the window.'''
        event = sdl2.SDL_Event()
        while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == sdl2.SDL_QUIT:
                return True
        return False

    def close(self) -> None:
        sdl2.SDL_DestroyTexture(self.__texture)
        sdl2.SDL_DestroyRenderer(self.__renderer)
        sdl2.SDL_DestroyWindow(self.__window)
        sdl2.SDL_Quit()
